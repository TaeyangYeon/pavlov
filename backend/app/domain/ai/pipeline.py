"""AnalysisPipeline orchestrator for Step 10: AI Response Parser & Validation Pipeline."""
from datetime import date

from app.domain.ai.client import AIClient
from app.domain.ai.prompt_builder import build_prompt
from app.domain.ai.schemas import AIPromptInput, AIPromptOutput
from app.domain.ai.validators import validate_ai_output_with_context
from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository


class AnalysisPipeline:
    """
    Orchestrates the complete AI analysis pipeline.
    
    Pipeline: FilterChain output → AIPromptBuilder → AnthropicClient → AIResponseValidator
    
    This pipeline connects all Phase 2 components and provides:
    - Unified orchestration
    - Enhanced validation with hallucination defense
    - Analysis log persistence for Step 17
    - Clean abstraction boundary
    """

    def __init__(
        self,
        ai_client: AIClient,
        analysis_log_repository: AnalysisLogRepository
    ):
        """Initialize pipeline with dependency injection."""
        self._ai_client = ai_client
        self._analysis_log_repository = analysis_log_repository

    async def run(
        self,
        prompt_input: AIPromptInput,
        analysis_date: date
    ) -> AIPromptOutput | None:
        """
        Execute the complete analysis pipeline.
        
        Returns:
            AIPromptOutput if successful and valid, None if validation failed
            
        Raises:
            AICallError: If AI service call fails after retries
        """
        try:
            # Step 1: Build prompt from input
            prompt = build_prompt(prompt_input)

            # Step 2: Call AI service
            ai_output = await self._ai_client.call(prompt)

            # Step 3: Enhanced validation with hallucination defense
            valid_tickers = [stock.ticker for stock in prompt_input.filtered_stocks]
            validation_result = validate_ai_output_with_context(ai_output, valid_tickers)

            if validation_result.is_valid:
                # Success: Save log with executed=True
                await self._analysis_log_repository.save(
                    date=analysis_date,
                    market=prompt_input.market,
                    executed=True,
                    ai_response=ai_output.model_dump()
                )
                return ai_output
            else:
                # Validation failed: Save log with executed=False
                error_message = f"Validation failed: {'; '.join(validation_result.errors)}"
                await self._analysis_log_repository.save(
                    date=analysis_date,
                    market=prompt_input.market,
                    executed=False,
                    error_message=error_message
                )
                return None

        except Exception as e:
            # AI call or other error: Save log with executed=False
            await self._analysis_log_repository.save(
                date=analysis_date,
                market=prompt_input.market,
                executed=False,
                error_message=str(e)
            )
            # Re-raise the exception to maintain error propagation
            raise
