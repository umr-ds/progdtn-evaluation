from core.services.coreservices import CoreService


class ContextGeneratorService(CoreService):
    """Generates semi-random node context"""

    name = "ContextGenerator"
    executables = ("context_generator", )
    dependencies = ("DTN7", )
    startup = ('bash -c "nohup context_generator &2>1 | tee context.log &"', )

    @classmethod
    def generate_config(cls, node, filename):
        pass
