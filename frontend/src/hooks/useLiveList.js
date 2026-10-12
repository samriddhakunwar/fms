import { useCallback, useEffect, useState } from "react";
import api, { getErrorMessage } from "../services/api";

const SEARCH_DELAY_MS = 300;

/**
 * Loads a list endpoint and reloads it as `search` (debounced) or `filters`
 * (immediately) change. A newer request cancels the older one, so a slow
 * response for "p" can never replace the results for "pen".
 *
 * `loading` is only true until the first response; `busy` covers every
 * request after that, so the table keeps showing rows while the user types.
 */
export default function useLiveList(url, search = "", filters = {}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [term, setTerm] = useState(search.trim());
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setTerm(search.trim()), SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [search]);

  const filterKey = JSON.stringify(filters);

  useEffect(() => {
    const controller = new AbortController();
    const params = Object.fromEntries(
      Object.entries(JSON.parse(filterKey)).filter(([, value]) => value)
    );
    if (term) params.search = term;

    setBusy(true);
    api
      .get(url, { params, signal: controller.signal })
      .then(({ data }) => {
        setItems(data);
        setError("");
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(getErrorMessage(err));
      })
      .finally(() => {
        if (controller.signal.aborted) return;
        setBusy(false);
        setLoading(false);
      });
    return () => controller.abort();
  }, [url, term, filterKey, version]);

  const reload = useCallback(() => setVersion((value) => value + 1), []);

  return { items, loading, busy, error, reload, searching: Boolean(term) };
}
