// view/assets/js/chatbot_llm.js
'use strict';

if (typeof self.pipeline === 'undefined') {
    console.error("Transformers.js (pipeline) not loaded. LLM functionality will not work.");
    self.llmReady = false;
    window.dispatchEvent(new CustomEvent('llm-error', { detail: { message: "Transformers.js library not loaded."} }));
} else {
    self.llmReady = false;
    self.llmPipeline = null;
    self.llmModelName = 'Xenova/distilgpt2';

    console.log(`Attempting to load LLM model: ${self.llmModelName}`);
    window.dispatchEvent(new CustomEvent('llm-loading'));

    (async () => {
        try {
            self.llmPipeline = await self.pipeline('text-generation', self.llmModelName, {
                progress_callback: (data) => {
                    console.log('LLM loading progress:', data);
                    if (data.status === 'ready' && data.name === self.llmModelName && data.file.endsWith('.onnx')) {
                        if (!self.llmReady) {
                            self.llmReady = true;
                            console.log('LLM is ready.');
                            window.dispatchEvent(new CustomEvent('llm-ready'));
                        }
                    }
                }
            });
            if (!self.llmReady && self.llmPipeline) { // Fallback if specific progress event not caught
                 self.llmReady = true;
                 console.log('LLM reported as ready by pipeline completion (fallback).');
                 window.dispatchEvent(new CustomEvent('llm-ready'));
            }
        } catch (error) {
            console.error('Error loading LLM model:', error);
            self.llmReady = false;
            window.dispatchEvent(new CustomEvent('llm-error', { detail: error }));
        }
    })();

    self.getLLMResponse = async function(inputText, maxNewTokens = 50) {
        if (!self.llmReady || !self.llmPipeline) {
            console.warn('LLM not ready or pipeline not initialized for input:', inputText);
            return "El asistente no está listo en este momento. Intenta de nuevo más tarde.";
        }

        try {
            console.log(`Sending to LLM: "${inputText}"`);
            let prompt = inputText;

            let outputs = await self.llmPipeline(prompt, {
                max_new_tokens: maxNewTokens,
                num_return_sequences: 1,
                temperature: 0.7,
                top_k: 50,
                do_sample: true,
            });

            console.log("LLM Raw Output:", outputs);
            let generatedText = outputs[0].generated_text;

            // Remove the prompt from the beginning of the generated text if present
            if (generatedText.toLowerCase().startsWith(prompt.toLowerCase())) {
                 generatedText = generatedText.substring(prompt.length);
            }

            // Remove common end-of-text tokens and trim whitespace
            generatedText = generatedText.replace(/<\|endoftext\|>/g, '').replace(/\[EOS\]/g, '').trim();

            if (!generatedText) {
                generatedText = "No pude generar una respuesta clara. Intenta reformular tu pregunta.";
            }

            console.log("LLM Cleaned Output:", generatedText);
            return generatedText;
        } catch (error) {
            console.error('Error during LLM generation:', error);
            return "Hubo un error al generar la respuesta.";
        }
    };
}
