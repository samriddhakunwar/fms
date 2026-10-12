from rest_framework import filters

MAX_SEARCH_LENGTH = 100


class PrefixSearchFilter(filters.SearchFilter):
    """
    ?search= for the list pages: every field in search_fields matches from its
    start, case-insensitively, and the whole query is one term, so "ram ba"
    finds "Ram Bahadur" (DRF's default would split it into two words).
    """

    def get_search_terms(self, request):
        value = request.query_params.get(self.search_param, "")
        value = value.replace("\x00", "").strip()[:MAX_SEARCH_LENGTH]
        return [value] if value else []

    def construct_search(self, field_name, queryset=None):
        return f"{field_name.lstrip('^=@$')}__istartswith"
