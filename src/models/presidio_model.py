from typing import Any, Dict, List, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_anonymizer import AnonymizerEngine, OperatorConfig

from src.guardrails.pii_types import PII_ENTITY_TYPE_MAP


class PresidioModel:
    """
    A model for PII detection and anonymization using Microsoft Presidio.
    """
    def __init__(self):
        self.analyzer = AnalyzerEngine(nlp_engine=SpacyNlpEngine())
        self.anonymizer = AnonymizerEngine()

    def analyze_text(self, text: str, entities: List[str], language: str = 'en'):
        """
        Analyze the text to detect specified entities.

        Args:
            text: The text to analyze.
            entities: List of entities to detect.
            language: Language of the text.

        Returns:
            List of detected entities.
        """
        # Convert PIIEntityType to string values for Presidio
        return self.analyzer.analyze(text=text, entities=entities, language=language)

    def anonymize_text(self, text: str, analyzer_results: List[Dict[str, Any]]) -> object:
        """
        Anonymize the text based on the analysis results.

        Args:
            text: The text to anonymize.
            analyzer_results: Results from the analyzer.

        Returns:
            Anonymized text.
        """
        return self.anonymizer.anonymize(text=text, analyzer_results=analyzer_results,
                                        operators={"DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})})

    def process_text(self, text: str, options: Dict[str, Any] = None) -> Tuple[str, List[Dict[str, str]]]:
        """
        Process input text to detect and obscure PII.
        
        Args:
            text: Input text to process
            options: Dictionary of options for processing (not used in this implementation)
            
        Returns:
            Tuple containing:
            - Processed text with PII obscured
            - List of detected PII entities
        """
        # Analyze the text
        analyzer_results = self.analyze_text(text, [PII_ENTITY_TYPE_MAP[entity] for entity in options.get('entity_types')])
        # Anonymize the text
        anonymized_output = self.anonymize_text(text, analyzer_results)

        # Convert analyzer results to the expected format
        entities = [
            {
                "text": text[result.start:result.end],
                "label": result.entity_type,
                "start": result.start,
                "end": result.end
            }
            for result in analyzer_results
        ]

        return anonymized_output.text, entities 