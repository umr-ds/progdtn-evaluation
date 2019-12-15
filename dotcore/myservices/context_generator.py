from core.services.coreservices import CoreService


class ContextGeneratorService(CoreService):
    """Generates semi-random node context"""

    name = "ContextGenerator"
    executables = ("context_generator", )
    dependencies = ("dtn7", )
    startup = (f'bash -c "context_generator &> context.log &"', )

    @classmethod
    def generate_config(cls, node, filename):
        pass
