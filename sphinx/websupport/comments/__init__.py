# -*- coding: utf-8 -*-
"""
    sphinx.websupport.comments
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Comments for the websupport package.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

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
        raise NotImplementedError()
    
    def get_node(self, node_id):
        raise NotImplementedError()

    def post_build(self):
        """Called after a build has completed. Use this to finalize the
        addition of nodes if needed.
        """
        pass

    def add_comment(self, parent_id, text, displayed, 
                    username, rating, time, proposal, proposal_diff):
        """Called when a comment is being added."""
        raise NotImplementedError()

    def get_comment(self, comment_id):
        raise NotImplementedError()

    def get_comments(self, parent_id, user_id):
        """Called to retrieve all comments for a node."""
        raise NotImplementedError()

    def process_vote(self, comment_id, user_id, value):
        raise NotImplementedError()
