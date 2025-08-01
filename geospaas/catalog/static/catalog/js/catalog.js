"use strict";

class APIObject extends HTMLElement {
  constructor() {
    super();
    this._api_data = null;
    this._html_repr = null;
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

  get style() {
    return this._html_repr.style;
  }

  connectedCallback() {
    this.make_html_repr();
    this.insertAdjacentElement("afterbegin", this._html_repr);
  }
}

class Dataset extends APIObject {
  constructor() {
    super();
    this._expanded = false;
    this._footprint = null;
  }

  get title() {
    return this.api_data.entry_id;
  }

  collapse() {
    for(let tb of this._html_repr.tBodies) {tb.hidden = true;}
    this._expanded = false;
  }

  expand() {
    for(let tb of this._html_repr.tBodies) {tb.hidden = false;}
    this._expanded = true;
  }

  toggle() {
    if(this._expanded) {this.collapse();}
    else {this.expand();}
  }

  make_html_repr() {
    this._html_repr = document.createElement("table");
    let header = document.createElement("th");
    header.colSpan = 2;
    header.appendChild(document.createTextNode(this.title));
    this._html_repr.createTHead().insertRow().appendChild(header);
    let tbody = this._html_repr.createTBody();
    let newRow;
    for(let key in this.api_data) {
      newRow = tbody.insertRow();
      newRow.insertCell().appendChild(document.createTextNode(key));
      newRow.insertCell().appendChild(document.createTextNode(this.api_data[key]));
    }
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
    this.collapse();
    this.addEventListener("click", () => this.toggle());
    this.display_footprint();
    this.setup_footprint_highlight();
  }

  disconnectedCallback() {
    if (this._footprint != null) {
      this._footprint.removeFrom(window.maps[0]);
    }
  }
}
customElements.define("geospaas-dataset", Dataset);

class Tag extends APIObject {
  make_html_repr() {
    this._html_repr = document.createElement("div");
    this._html_repr.appendChild(document.createTextNode(`${this._api_data.name}: ${this._api_data.value}`));
  }
}
customElements.define("geospaas-tag", Tag);

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
  let tags = document.getElementById("selected_tags").childNodes;
  // let keywords = document.getElementById("id_keywords").value;
  // let full_text = document.getElementById("id_full_text").value;
  // let parameters = document.getElementById("id_parameters").value;

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
  fetch(`${url}?` + new URLSearchParams(full_request_parameters).toString())
    .then(response => response.json())
    .then(page => display_page(page))
    .catch(error => console.log(`${error}: Failed to get datasets`));
}

function add_search_tag(tag, selected_tags) {
  for(let existing_tag of selected_tags.childNodes) {
    if(existing_tag.api_data.id === tag.api_data.id) {return null;}
  }
  let selected_tag = document.createElement("geospaas-tag");
  selected_tag.api_data = tag.api_data;
  selected_tags.appendChild(selected_tag);

  selected_tag.style.display = "flex";
  selected_tag.style.marginRight = "4px";
  selected_tag.style.marginLeft = "4px";
  selected_tag.style.background = "#c2f3fc";

  // make close button that removes the tag
  let close_button = document.createElement("div");
  close_button.style.marginLeft = "2px";
  close_button.style.fontSize = "14px";
  close_button.style.color = "#018096";
  close_button.style.cursor = "pointer";

  close_button.appendChild(document.createTextNode("X"));
  close_button.addEventListener("click", () => {
    selected_tag.parentNode.removeChild(selected_tag);
  });

  selected_tag._html_repr.appendChild(close_button);
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
  let tag_search_box = document.getElementById("id_tags");
  let selected_tags = document.createElement("div");
  selected_tags.id = "selected_tags";
  selected_tags.style.display = "flex";
  tag_search_box.after(selected_tags);

  let tags_dropdown = document.createElement("div");
  tags_dropdown.style.position = "relative";
  tag_search_box.before(tags_dropdown);
  let tags_dropdown_contents = document.createElement("div");
  tags_dropdown_contents.id = "tags_dropdown_contents";
  tags_dropdown_contents.style.cssText = `
    position: absolute;
    top: ${tag_search_box.clientHeight}px;
    z-index: 10;
    max-height: ${tag_search_box.clientHeight * 5}px;
    width: ${tag_search_box.clientWidth}px;
    background-color: #f1f1f1;
    overflow: scroll;
  `;
  tags_dropdown.appendChild(tags_dropdown_contents);

  tag_search_box.addEventListener("input", (event) => {
    let tags_dropdown_contents = document.getElementById("tags_dropdown_contents");
    clear_children(tags_dropdown_contents);
    if(event.target.value.length >= 2) {
      fetch(`${window.location}api/tags/?` + new URLSearchParams({"value__icontains": tag_search_box.value}).toString())
        .then(response => response.json())
        .then(page => {
          for (let tag_data of page.results) {
            let tag = document.createElement("geospaas-tag")
            tag.api_data = tag_data;
            tag.addEventListener("click", () => {
              add_search_tag(tag, selected_tags);
            });
            tags_dropdown_contents.appendChild(tag);
          }
        })
        .catch(error => console.log(`${error}: Failed to get tags`));
    }
  });
});
