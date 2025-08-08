
export class APIObject extends HTMLElement {
    constructor() {
      super();
      this._api_data = null;
      this._html_repr = null;
    }

    static create(customElementName, api_data) {
      let element = document.createElement(customElementName);
      element.api_data = api_data;
      return element;
    }

    get api_data() {
      return this._api_data;
    }

    set api_data(dict) {
      this._api_data = dict;
    }

    make_html_repr() {
      throw new Error("make_html_repr() must be implemented");
    }

    get_style() {
      return "";
    }

    connectedCallback() {
      this.make_html_repr();
      const shadow = this.attachShadow({ mode: "open" });
      shadow.appendChild(this._html_repr);

      const sheet = new CSSStyleSheet();
      sheet.replaceSync(this.get_style());
      shadow.adoptedStyleSheets = [sheet];
    }
  }
