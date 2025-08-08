"use strict";

import {APIObject} from "/static/base_viewer/js/geospaas_api.js"

customElements.define("geospaas-dataset", class extends APIObject {
  constructor() {
    super();
    this._footprint = null;
    this._text_fields = {
      "entry_id": "ID",
      "entry_title": "Title",
      "time_coverage_start": "Start",
      "time_coverage_end": "End",
      "summary": "Summary",
    };
    this._related_fields = {
      "tags": {"title": "Tags", "element": "geospaas-tag"},
      "keywords": {"title": "Keywords", "element": "geospaas-keyword"},
      "parameters": {"title": "Parameters", "element": "geospaas-parameter"},
    };
  }

  get title() {
    return this.api_data.entry_id;
  }

  get_style() {
    return `
      table {
        table-layout: fixed;
        width: 100%;
      }

      table th {
        font-weight: normal;
        text-align: left;
      }`;
  }

  make_html_repr() {
    this._html_repr = document.createElement("table");
    let header = document.createElement("th");
    header.colSpan = 2;
    header.appendChild(document.createTextNode(this.title));
    this._html_repr.createTHead().insertRow().appendChild(header);
    let tbody = this._html_repr.createTBody();
    tbody.hidden = true;
    let newRow;
    for(const key in this._text_fields) {
      if(this.api_data[key] && this.api_data[key].length) {
        newRow = tbody.insertRow();
        newRow.insertCell().appendChild(document.createTextNode(this._text_fields[key]));
        newRow.insertCell().appendChild(document.createTextNode(this.api_data[key]));
      }
    }
    for(const key in this._related_fields) {

      if(this.api_data[key] && this.api_data[key].length) {
        let value = this.api_data[key];
        if(Array.isArray(value)){
          newRow = tbody.insertRow();
          newRow.insertCell().appendChild(document.createTextNode(this._related_fields[key].title));
          let contents_cell = newRow.insertCell();

          // populate related objects lazily
          this.addEventListener("click", () => {
            if(!this._related_fields[key].resolved) {
              for(let url of this.api_data[key]) {
                fetch(url)
                .then(response => response.json())
                .then(page => {
                  contents_cell.appendChild(APIObject.create(this._related_fields[key].element, page));
                })
                .catch(error => console.log(`${error}: Failed to get object from API`))
              }
              this._related_fields[key].resolved = true;
            }
          });
        }
      }
    }
    this.addEventListener("click", () => {
      for(let tb of this._html_repr.tBodies) {
        if(tb.hidden) {tb.hidden = false} else {tb.hidden = true};
      }
    });
  }

  display_footprint() {
    let location = this._api_data.location;
    if(location != null) {
      if (location.startsWith("SRID")) {location = location.split(";")[1];}
      this._footprint = new L.geoJSON(
        Terraformer.wktToGeoJSON(location),
        {
          style: {
          "color": "#0000ff",
          "weight": 1,
          "opacity": 0.9,
          "fillOpacity": 0.1,
          }
        }
      ).addTo(window.maps[0]);
    }
  }

  setup_footprint_highlight() {
    // highlight when hovering over table
    this.addEventListener("mouseover", () => {
      if (this._footprint != null) {this._footprint.setStyle({color: '#ff0000'});}
      this._html_repr.style.backgroundColor = 'lightblue';
    });
    this.addEventListener("mouseout", () => {
      if (this._footprint != null) {this._footprint.setStyle({color: '#0000ff'});}
      this._html_repr.style.backgroundColor = 'azure';
    });

    // highlight when hovering over map
    if (this._footprint != null) {
      this._footprint.addEventListener("mouseover", () => {
        this._html_repr.style.backgroundColor = 'lightblue';
        this._footprint.setStyle({color: '#ff0000'});
      });
      this._footprint.addEventListener("mouseout", () => {
        this._html_repr.style.backgroundColor = 'azure';
        this._footprint.setStyle({color: '#0000ff'});
      });
    }
  }

  connectedCallback() {
    super.connectedCallback();
    this.display_footprint();
    this.setup_footprint_highlight();
  }

  disconnectedCallback() {
    if (this._footprint != null) {
      this._footprint.removeFrom(window.maps[0]);
    }
  }
});

customElements.define("geospaas-tag", class extends APIObject {
  make_html_repr() {
    this._html_repr = document.createElement("div");
    this._html_repr.appendChild(document.createTextNode(`${this._api_data.name}: ${this._api_data.value}`));
  }
});

customElements.define("geospaas-keyword", class extends APIObject {
  make_html_repr() {
    this._html_repr = document.createElement("div");
    let display_name = null;
    if("Short_Name" in this._api_data.data) {
      display_name = this._api_data.data.Short_Name;
    } else {
      display_name = String(this._api_data.data);
    }
    this._html_repr.appendChild(document.createTextNode(`${this._api_data.kind}(${this._api_data.version}): ${display_name}`));
  }
});

customElements.define("geospaas-parameter", class extends APIObject {
  make_html_repr() {
    this._html_repr = document.createElement("div");
    let display_name = null;
    if("standard_name" in this._api_data.data) {
      display_name = this._api_data.data.standard_name;
    } else if("short_name" in this._api_data.data) {
      display_name = this._api_data.data.short_name;
    } else {
      display_name = String(this._api_data.data);
    }
    this._html_repr.appendChild(document.createTextNode(display_name));
  }
});


function display_page(page) {
  // clear existing contents
  let datasets_table = document.getElementById("datasets_table");
  // add the current page of datasets to the table
  if(page.results){
    datasets_table.querySelectorAll("tbody > tr").forEach((row) => {row.remove()});
    let newRow;
    let newCell;
    let dataset;
    for(let dataset_json of page.results) {
      dataset = document.createElement("geospaas-dataset");
      dataset.api_data = dataset_json;
      newRow = datasets_table.querySelector('tbody').insertRow();
      newCell = newRow.insertCell();
      newCell.appendChild(dataset);
    }
  }

  // deal with cursor pagination
  let previous_button = document.getElementById("datasets_previous_button");
  let next_button = document.getElementById("datasets_next_button");
  if(page.previous) {
    let previous_url = new URL(page.previous);
    previous_button.setAttribute("data-cursor", previous_url.searchParams.get('cursor'));
    previous_button.disabled = false;
  } else {
    previous_button.disabled = true;
  }
  if(page.next) {
    let next_url = new URL(page.next);
    next_button.setAttribute("data-cursor", next_url.searchParams.get('cursor'));
    next_button.disabled = false;
  } else {
    next_button.disabled = true;
  }
}

function get_datasets(url, request_parameters) {
  let full_request_parameters = {
    ...request_parameters,
  };
  let polygon = document.getElementById("id_polygon").value;
  let time_coverage_start = document.getElementById("id_time_coverage_start").value;
  let time_coverage_end = document.getElementById("id_time_coverage_end").value;
  let tags = document.getElementById("selected_geospaas-tag").childNodes;
  let keywords = document.getElementById("selected_geospaas-keyword").childNodes;
  let parameters = document.getElementById("selected_geospaas-parameter").childNodes;

  if(polygon) {full_request_parameters.location__intersects = polygon;}
  if(time_coverage_start) {full_request_parameters.time_coverage_end__gte = time_coverage_start;}
  if(time_coverage_end) {full_request_parameters.time_coverage_start__lte = time_coverage_end;}
  if(tags.length !== 0) {
    let tag_ids = [];
    for(let tag of tags) {
      tag_ids.push(tag.api_data.id);
    }
    full_request_parameters.tags__id__in = tag_ids.join(",");
  }
  if(keywords.length !== 0) {
    let keyword_ids = [];
    for(let keyword of keywords) {
      keyword_ids.push(keyword.api_data.id);
    }
    full_request_parameters.keywords__id__in = keyword_ids.join(",");
  }
  if(parameters.length !== 0) {
    let parameter_ids = [];
    for(let parameter of parameters) {
      parameter_ids.push(parameter.api_data.id);
    }
    full_request_parameters.parameters__id__in = parameter_ids.join(",");
  }
  fetch(`${url}?` + new URLSearchParams(full_request_parameters).toString())
    .then(response => response.json())
    .then(page => display_page(page))
    .catch(error => console.log(`${error}: Failed to get datasets`));
}

function make_selector_field(search_box, api_element_name, api_url, api_filter) {
  /* Make a text input field search for GeoSPaaS API objects to be used
     in the datasets search form */
  search_box.parentNode.style.display = "flex";
  let selected_elements = document.createElement("div");
  selected_elements.id = `selected_${api_element_name}`;
  selected_elements.style.display = "flex";
  search_box.after(selected_elements);

  let dropdown = document.createElement("div");
  dropdown.style.position = "relative";
  dropdown.setAttribute("tabindex", 0)
  search_box.before(dropdown);
  let dropdown_contents = document.createElement("div");
  dropdown_contents.id = `dropdown_contents_${api_element_name}`;
  dropdown_contents.style.cssText = `
    position: absolute;
    top: ${search_box.clientHeight}px;
    z-index: 10;
    max-height: ${search_box.clientHeight * 5}px;
    width: ${search_box.clientWidth}px;
    background-color: #f1f1f1;
    overflow: scroll;
  `;
  dropdown.appendChild(dropdown_contents);

  search_box.addEventListener("input", (event) => {
    clear_children(dropdown_contents);
    if(event.target.value.length >= 2) {
      fetch(api_url + new URLSearchParams({[api_filter]: search_box.value}).toString())
        .then(response => response.json())
        .then(page => {
          for (let api_data of page.results) {
            let api_element = APIObject.create(api_element_name, api_data);
            api_element.addEventListener("click", () => {
              add_search_element(api_element, selected_elements);
            });
            dropdown_contents.appendChild(api_element);
          }
        })
        .catch(error => console.log(`${error}: Failed to get objects from API`));
    }
  });
  search_box.addEventListener("focusout", (event) => {
    if(event.relatedTarget !== dropdown) {
      search_box.value = "";
      search_box.dispatchEvent(new Event("input"));
    } else {
      search_box.focus();
    }
  });
}

function add_search_element(element, selected_elements) {
  for(let existing_element of selected_elements.childNodes) {
    if(existing_element.api_data.id === element.api_data.id) {return null;}
  }
  let selected_element = element.cloneNode(true);
  selected_element.api_data = element.api_data;
  selected_elements.appendChild(selected_element);

  selected_element.style.marginRight = "4px";
  selected_element.style.marginLeft = "4px";
  selected_element.style.background = "#c2f3fc";

  // make close button that removes the tag
  let close_button = document.createElement("div");
  close_button.style.marginLeft = "2px";
  close_button.style.fontSize = "14px";
  close_button.style.color = "#018096";
  close_button.style.cursor = "pointer";

  selected_element._html_repr.style.display = "flex";
  close_button.appendChild(document.createTextNode("X"));
  close_button.addEventListener("click", () => {
    selected_element.parentNode.removeChild(selected_element);
  });
  selected_element._html_repr.appendChild(close_button);
}

function clear_children(parent) {
  for(let i=parent.childNodes.length-1;i>-1;i--) {
    parent.removeChild(parent.childNodes[i]);
  }
}

document.addEventListener("DOMContentLoaded", function() {
  // add listeners to trigger datasets search
  let host = `${window.location.protocol}//${window.location.host}`
  document.querySelectorAll(
    "#dataset_search_button, #datasets_previous_button, #datasets_next_button"
  ).forEach((element) => element.addEventListener(
    "click",
    function() {
      let parameters = {page_size: document.getElementById("datasets_page_size").value};
      let cursor = this.getAttribute('data-cursor');
      if(cursor) {parameters.cursor = cursor;}
      get_datasets(`${host}${this.getAttribute('data-path')}`, parameters);
    }
  ));

  // trigger Search click if user presses enter on page size field
  document.getElementById("datasets_page_size").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      document.getElementById("dataset_search_button").click();
    }
  });

  // tag search field
  make_selector_field(
    document.getElementById("id_tags"), "geospaas-tag",
    `${window.location}api/tags/?`, "value__icontains");
  // keyword search field
  make_selector_field(
    document.getElementById("id_keywords"), "geospaas-keyword",
    `${host}/vocabularies/api/keywords/?`, "data__icontains");
  // parameters search field
  make_selector_field(
    document.getElementById("id_parameters"), "geospaas-parameter",
    `${host}/vocabularies/api/parameters/?`, "data__icontains");
});
