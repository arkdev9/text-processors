import logging
from transformers import pipeline
from transformers.models.auto.modeling_auto import AutoModelForSeq2SeqLM
from typing import List, Optional
from haystack import Document

logger = logging.getLogger(__name__)


class Summarizer:
    def __init__(
        self,
        model_name_or_path: str = "sshleifer/distilbart-cnn-12-6",
        tokenizer: Optional[str] = None,
        max_length: int = 200,
        min_length: int = 100,
        use_gpu: int = -1,
        clean_up_tokenization_spaces: bool = True,
        separator_for_single_summary: str = " ",
    ):
        """
        Load a Summarization model from Transformers.
        See the up-to-date list of available models on
        `huggingface.co/models <https://huggingface.co/models?filter=summarization>`__

        :param model_name_or_path: Directory of a saved model or the name of a public model e.g.
                                'facebook/rag-token-nq', 'facebook/rag-sequence-nq'.
                                See https://huggingface.co/models?filter=summarization for full list of available models.
        :param tokenizer: Name of the tokenizer (usually the same as model)
        :param max_length: Maximum length of summarized text
        :param min_length: Minimum length of summarized text
        :param use_gpu: If < 0, then use cpu. If >= 0, this is the ordinal of the gpu to use
        :param clean_up_tokenization_spaces: Whether or not to clean up the potential extra spaces in the text output
        :param separator_for_single_summary: If `generate_single_summary=True` in `predict()`, we need to join all docs
                                            into a single text. This separator appears between those subsequent docs.
        """
        if tokenizer is None:
            tokenizer = model_name_or_path
        model = AutoModelForSeq2SeqLM.from_pretrained(
            pretrained_model_name_or_path=model_name_or_path
        )
        self.summarizer = pipeline(
            "summarization", model=model, tokenizer=tokenizer, device=use_gpu
        )
        self.max_length = max_length
        self.min_length = min_length
        self.clean_up_tokenization_spaces = clean_up_tokenization_spaces
        self.separator_for_single_summary = separator_for_single_summary

    def predict(
        self,
        min_length,
        max_length,
        documents: List[Document],
        generate_single_summary: bool = False,
    ) -> List[Document]:
        self.min_length = min_length
        self.max_length = max_length
        """
        Produce the summarization from the supplied documents.
        These document can for example be retrieved via the Retriever.

        :param documents: Related documents (e.g. coming from a retriever) that the answer shall be conditioned on.
        :param generate_single_summary: Whether to generate a single summary for all documents or one summary per document.
                                        If set to "True", all docs will be joined to a single string that will then
                                        be summarized.
                                        Important: The summary will depend on the order of the supplied documents!
        :return: List of Documents, where Document.text contains the summarization and Document.meta["context"]
                 the original, not summarized text
        """

        if self.min_length > self.max_length:
            raise AttributeError("min_length cannot be greater than max_length")

        if len(documents) == 0:
            raise AttributeError(
                "Summarizer needs at least one document to produce a summary."
            )

        contexts: List[str] = [doc.text for doc in documents]
        print("MIN LENGTH: {} MAX LENGTH: {}".format(self.min_length,self.max_length))
        if generate_single_summary:
            # Documents order is very important to produce summary.
            # Different order of same documents produce different summary.
            contexts = [self.separator_for_single_summary.join(contexts)]

        summaries = self.summarizer(
            contexts,
            min_length=self.min_length,
            max_length=self.max_length,
            return_text=True,
            num_beams = 2,
            clean_up_tokenization_spaces=self.clean_up_tokenization_spaces,
        )

        result: List[Document] = []

        for context, summarized_answer in zip(contexts, summaries):
            cur_doc = Document(
                text=summarized_answer["summary_text"], meta={"context": context}
            )
            result.append(cur_doc)

        return result