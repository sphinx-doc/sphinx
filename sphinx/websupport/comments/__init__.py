
class StorageBackend(object):
    def pre_build(self):
        """Called immediately before the build process begins. Use this
        to prepare the StorageBackend for the addition of nodes.
        """
        pass

    def add_node(self, document, line, source, treeloc):
        """Add a node to the StorageBackend.

        `document` is the name of the document the node belongs to.
        
        `line` is the line in the source where the node begins.

        `source` is the source files name.
        
        `treeloc` is for future use.
        """
        raise NotImplemented
    
    def post_build(self):
        """Called after a build has completed. Use this to finalize the
        addition of nodes if needed.
        """
        pass

    def add_comment(self, parent_id, text, displayed, username, 
                    rating, time):
        """Called when a comment is being added."""
        raise NotImplemented

    def get_comments(self, parent_id):
        """Called to retrieve all comments for a node."""
        raise NotImplemented
