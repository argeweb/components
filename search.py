from argeweb.core import search as argeweb_search


class Search(object):
    """
    Provides a simple high-level interface to searching items in the App Engine Search API and
    utilizes the search helpers in :mod:`argeweb.core.search`.
    """

    def __init__(self, controller):
        self.controller = controller

    def _get_index(self):
        if hasattr(self.controller.meta, 'search_index'):
            return self.controller.meta.search_index
        if hasattr(self.controller.meta, 'Model'):
            Model = self.controller.meta.Model
            if hasattr(Model.Meta, 'search_index'):
                return Model.Meta.search_index[0] if isinstance(Model.Meta.search_index, (list, tuple)) else Model.Meta.search_index
            return 'auto_ix_%s' % Model._get_kind()
        raise ValueError('No search index could be determined')

    def _converter_language(self, query_string):
        if hasattr(self.controller.meta, 'Model'):
            Model = self.controller.meta.Model
            for filed_name, f in Model._properties.items():
                query_string = query_string.replace(f._verbose_name, filed_name)
        return query_string

    def search(self, index=None, query=None, limit=None, cursor=None, sort_field=None, sort_direction='asc', sort_default_value=None, options=None, return_all=False):
        """
        Searches using the provided index (or an automatically determine one).

        Expects the search query to be in the ``query`` request parameter.

        Also takes care of setting pagination information if the :mod:`pagination component <argeweb.components.pagination>` is present.

        See :func:`argeweb.core.search.search` for more details.
        """

        index = index if index else self._get_index()
        query_string = query if query else self.controller.request.params.get('query', '')
        query_string = self._converter_language(query_string)
        options = options if options else {}
        search_function = self.controller.meta.search_function if hasattr(self.controller.meta, 'search_function') else argeweb_search.search

        if 'pagination' in self.controller.components:
            cursor, limit = self.controller.components.pagination.get_pagination_params(cursor, limit)

        error, results, cursor, next_cursor = search_function(
            index,
            query_string,
            cursor=cursor,
            limit=limit,
            options=options,
            sort_field=sort_field,
            sort_direction=sort_direction,
            sort_default_value=sort_default_value)

        if error:
            self.controller.context['search_error'] = error

        if 'pagination' in self.controller.components:
            self.controller.components.pagination.set_pagination_info(
                current_cursor=cursor,
                next_cursor=next_cursor,
                limit=limit,
                count=len(results))

        self.controller.context['search_query'] = query_string
        self.controller.context['search_results'] = results

        if hasattr(self.controller, 'scaffold'):
            self.controller.context[self.controller.scaffold.plural] = results
        if return_all:
            return {
                'search_error': error,
                'search_query': query_string,
                'search_results': results,
                'paging': self.controller.context['paging'],
            }
        return results

    __call__ = search
