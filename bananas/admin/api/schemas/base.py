class BananasBaseRouter(object):
    def get_default_basename(self, viewset):
        return viewset.get_admin_meta().basename

    def get_schema_view(self):
        raise NotImplementedError
