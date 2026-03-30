class Reconciler:
    def __init__(self, factory_spec):
        self.spec = factory_spec

    async def reconcile_all(self):
        return {dept: "healthy" for dept in self.spec.active_departments}
