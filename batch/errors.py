"""Error definitions for Batch module."""


class BatchError(Exception):
    """Base exception for Batch module."""
    pass


class PipelineError(BatchError):
    """Raised when pipeline execution fails."""
    pass


class StageError(BatchError):
    """Raised when a specific pipeline stage fails."""
    def __init__(self, stage: str, message: str, original_error: Exception = None):
        self.stage = stage
        self.original_error = original_error
        super().__init__(f"Stage '{stage}' failed: {message}")
