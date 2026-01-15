export class APIObject {
    constructor(url = null, data = null) {
    // Validate inputs: exactly one of url or data must be provided
    if ((url && data) || (!url && !data)) {
      throw new Error("Exactly one of 'url' or 'data' must be provided");
    }

    this._url = url;
    this._data = data || {};
    this._isLoaded = Boolean(data);  // Track whether data has been loaded
    this._loadPromise = null;  // Cache the fetch promise to avoid multiple requests
    this._cache = {};  // Cache fetched related objects
    this._relatedFields = [];  // Lazily computed on first access

    // If initialized with data, extract the URL from it
    if (data && !url) {
      this._url = data.url || null;
    }
  }

   /**
   * Ensure data is loaded (fetch if initialized with URL only)
   */
  async ensureLoaded() {
    if (this._isLoaded) {
      return;
    }

    // Prevent multiple simultaneous fetch requests
    if (!this._loadPromise) {
      this._loadPromise = (async () => {
        try {
          const response = await fetch(this._url);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status} from ${this._url}`);
          }
          this._data = await response.json();
          this._isLoaded = true;
        } catch (error) {
          console.error(`Failed to fetch data from ${this._url}:`, error);
          throw error;
        }
      })();
    }

    await this._loadPromise;
  }

  /**
   * Detect which fields are related objects by examining their values.
   * Related fields are:
   * - Strings that look like URLs (start with http://, https://, or /)
   * - Arrays of strings (each being a URL)
   *
   * Returns a map of { fieldName: { type: 'single'|'array', urls: [...] } }
   */
  _detectRelatedFields() {
    if (this._relatedFields) {
      return this._relatedFields;
    }

    const related = {};

    for (const [key, value] of Object.entries(this._data)) {
      // Skip common metadata fields
      if (key === 'url' || key === 'id') continue;

      if (typeof value === 'string' && this._isUrl(value)) {
        // Single URL reference
        related[key] = { type: 'single', urls: [value] };
      } else if (
        Array.isArray(value) &&
        value.length > 0 &&
        typeof value[0] === 'string' &&
        this._isUrl(value[0])
      ) {
        // Array of URLs
        related[key] = { type: 'array', urls: value };
      }
    }

    this._relatedFields = related;
    return related;
  }

  /**
   * Check if a string looks like a URL
   */
  _isUrl(value) {
    return typeof value === 'string' && (
      value.startsWith('http://') ||
      value.startsWith('https://') ||
      value.startsWith('/')
    );
  }

  /**
   * Get a field value. Transparently handles both primitive and related fields:
   * - For primitive fields: returns the value as-is
   * - For related fields (URLs): fetches and returns APIObject(s)
   *
   * This provides a unified interface where callers don't need to distinguish
   * between primitive and related fields.
   *
   * @param {string} key - Field name
   * @returns {Promise<*>} Field value or APIObject(s) for related fields
   */
  async get(key) {
    await this.ensureLoaded();

    const value = this._data[key];
    if (value === undefined || value === null) {
      return null;
    }

    // Check if this is a related field
    const relatedFields = this._detectRelatedFields();
    if (key in relatedFields) {
      // Return cached result if available
      if (this._cache[key]) {
        return this._cache[key];
      }

      const fieldInfo = relatedFields[key];
      const urls = fieldInfo.urls;

      try {
        const results = await Promise.all(
          urls.map(url =>
            fetch(url)
              .then(response => {
                if (!response.ok) {
                  throw new Error(`HTTP ${response.status} from ${url}`);
                }
                return new APIObject(null, response.json());
              })
          )
        );

        // Return single model or array based on original field type
        this._cache[key] = fieldInfo.type === 'single' ? models[0] : models;
        return this._cache[key];
      } catch (error) {
        console.error(`Failed to fetch related field "${key}":`, error);
        throw error;
      }
    }

    // For primitive fields, return as-is
    return value;
  }

 /**
   * Fetch multiple fields at once (both primitive and related)
   *
   * @param {string[]} fieldNames - Array of field names to fetch
   * @returns {Promise<Object>} Object mapping field names to their values/APIObjects
   */
  async getMany(fieldNames) {
    const results = {};
    for (const field of fieldNames) {
      try {
        results[field] = await this.get(field);
      } catch (error) {
        results[field] = null;
      }
    }
    return results;
  }

  /**
   * Fetch all fields (both primitive and related)
   *
   * @returns {Promise<Object>} Object mapping all field names to their values/APIObjects
   */
  async getAll() {
    await this.ensureLoaded();
    return this.getMany(Object.keys(this._data));
  }

    /**
   * Check if data is currently loaded
   */
  isLoaded() {
    return this._isLoaded;
  }

  get url() {
    return this._url;
  }
}


export class APIObjectElement extends HTMLElement {
    constructor() {
      super();
      this._api_object = null;
      this._html_repr = null;
      this._fields = null;
    }

    static create(customElementName, api_object) {
      let element = document.createElement(customElementName);
      element.api_object = api_object;
      return element;
    }

    get api_object() {
      return this._api_object;
    }

    set api_object(data) {
      if (data instanceof APIObject) {
        this._api_object = data;
      } else if (data && typeof data === 'object') {
        // Wrap raw data in a model
        this._api_object = new APIObject(null, data);
      } else if (data && typeof data === 'string') {
        this._api_object = new APIObject(data, null);
      } else {
        this._model = null;
      }
    }

    makeHtmlRepr() {
      throw new Error("makeHtmlRepr() must be implemented");
    }

    getStyle() {
      return "";
    }

    async render() {
      if(!this._html_repr){
        await this.makeHtmlRepr();
      }
      const shadow = this.attachShadow({ mode: "open" });
      shadow.appendChild(this._html_repr);

      const sheet = new CSSStyleSheet();
      sheet.replaceSync(this.getStyle());
      shadow.adoptedStyleSheets = [sheet];
    }

    async connectedCallback() {
      await this.render();
    }
  }
