"""Optional LLM-as-judge modules. Requires pip install -e '.[eval]' and paid API credentials."""
def ragas_metrics():
    from ragas.metrics import LLMContextPrecisionWithoutReference, ResponseRelevancy
    return {'context_precision':LLMContextPrecisionWithoutReference,'response_relevancy':ResponseRelevancy}
def deepeval_metrics():
    from deepeval.metrics import FaithfulnessMetric,AnswerRelevancyMetric
    return {'faithfulness':FaithfulnessMetric,'answer_relevancy':AnswerRelevancyMetric}
