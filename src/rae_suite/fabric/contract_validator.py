from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

class ContractValidator:
    def validate_payload(self, model_class, data: dict) -> bool:
        try:
            model_class(**data)
            return True
        except ValidationError as e:
            logger.error(f"Contract violation: {e}")
            return False
