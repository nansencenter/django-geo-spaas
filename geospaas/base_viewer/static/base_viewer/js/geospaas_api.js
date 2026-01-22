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
    this._relatedFields = null;  // Lazily computed on first access

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
        related[key] = [value];
      } else if (
        Array.isArray(value) &&
        value.length > 0 &&
        typeof value[0] === 'string' &&
        this._isUrl(value[0])
      ) {
        // Array of URLs
        related[key] = value;
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

      const urls = relatedFields[key];

      try {
        const results = await Promise.all(
          urls.map(url =>
            fetch(url)
              .then(async response => {
                if (!response.ok) {
                  throw new Error(`HTTP ${response.status} from ${url}`);
                }
                return new APIObject(null, await response.json());
              })
          )
        );

        // Return single model or array based on original field type
        this._cache[key] = results;
        return results;
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
      this._resolved = false;
      this.getLabel = async e => await e.api_object.get('id');
      this.excludeFields = ['url', 'id'];
      this.fieldLabels = {};
      this.fieldFormatters = {};
    }

    static create(api_object, options={}, elementType='geospaas-object') {
      let element = document.createElement(elementType);
      element.api_object = api_object;
      if(options.getLabel) element.getLabel = options.getLabel;
      if(options.excludeFields) element.excludeFields = options.excludeFields;
      if(options.fieldLabels) element.fieldLabels = options.fieldLabels;
      if(options.fieldFormatters) element.fieldFormatters = options.fieldFormatters;
      return element;
    }

    get api_object() {
      return this._api_object;
    }

    set api_object(data) {
      if (data instanceof APIObject) {
        this._api_object = data;
      } else if (data && typeof data === 'object') {
        // initialized with raw API data
        this._api_object = new APIObject(null, data);
      } else if (data && typeof data === 'string') {
        // initialized with URL
        this._api_object = new APIObject(data, null);
      } else {
        this._model = null;
      }
    }

    // Returns a list of HTML elements representing the value
    _formatValue(key, value) {
      if (this.fieldFormatters[key]) {
        return this.fieldFormatters[key](value);
      }

      let values;
      if (!Array.isArray(value)) {
        values = [value];
      } else {
        values = value;
      }

      return values.map((i) => {
        if (i instanceof APIObject) {
          return APIObjectElement.create(i);
        } else {
          return document.createTextNode(String(i));
        }
      })
    }

    getFieldLabel(key) {
      return this.fieldLabels[key] ?? key
    }

    async makeHtmlRepr() {
      // create a table from a template
      let apiObjectTemplate = document.importNode(
        document.getElementById("geospaas-object-table-template").content,
        true);
      let apiObjectElement = apiObjectTemplate.getElementById("geospaas-object");
      let header = apiObjectElement.querySelector("#object-header");
      header.appendChild(document.createTextNode(await this.getLabel(this)));
      let attributesElement = apiObjectElement.querySelector("#object-attributes");
      attributesElement.hidden = true;
      this._html_repr = apiObjectElement;

      this.addEventListener("click", async () => {
        if (!this._resolved) {
          // populate attributes
          let attributeTemplateContent = apiObjectTemplate.getElementById("attribute-template").content;
          let newAttribute, attributeName, attributeValue, apiValue;
          let apiData = await this.api_object.getAll();
          for(const key in apiData ) {
            if (this.excludeFields.includes(key)) continue;
            apiValue = apiData[key];
            if(apiValue && apiValue.length) {
              newAttribute = document.importNode(attributeTemplateContent, true).getElementById("attribute");
              attributeName = newAttribute.querySelector("#attribute-name");
              attributeValue = newAttribute.querySelector("#attribute-value");

              attributeName.appendChild(document.createTextNode(this.getFieldLabel(key)));
              for (const htmlElement of this._formatValue(key, apiValue)) {
                attributeValue.appendChild(document.createElement('p').appendChild(htmlElement))
              }
              attributesElement.appendChild(newAttribute);
            }
            this._resolved = true;
          }
        }
      });

      this.addEventListener("click", (event) => {
        event.stopPropagation();
        for(let tb of apiObjectElement.tBodies) {
          if(tb.hidden) {tb.hidden = false} else {tb.hidden = true};
        }
      });
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

customElements.define("geospaas-object", APIObjectElement);
