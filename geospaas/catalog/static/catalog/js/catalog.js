"use strict";

class APIObject extends HTMLElement {
  constructor() {
    super();
    this._api_data = null;
    this._table = null;
    this._expanded = false;
  }

  get api_data() {
    return this._api_data;
  }

  set api_data(dict) {
    this._api_data = dict;
  }

  get title() {
    throw new Error("title getter must be implemented");
  }

  collapse() {
    for(let tb of this._table.tBodies) {tb.hidden = true;}
    this._expanded = false;
  }

  expand() {
    for(let tb of this._table.tBodies) {tb.hidden = false;}
    this._expanded = true;
  }

  toggle() {
    if(this._expanded) {this.collapse();}
    else {this.expand();}
  }

  make_table() {
    this._table = document.createElement("table");
    let header = document.createElement("th");
    header.colSpan = 2;
    header.appendChild(document.createTextNode(this.title));
    this._table.createTHead().insertRow().appendChild(header);
    let tbody = this._table.createTBody();
    let newRow;
    for(let key in this.api_data) {
      newRow = tbody.insertRow();
      newRow.insertCell().appendChild(document.createTextNode(key));
      newRow.insertCell().appendChild(document.createTextNode(this.api_data[key]));
    }
  }

  connectedCallback() {
    this.make_table();
    this.insertAdjacentElement("afterbegin", this._table);
    this.collapse();
    this.addEventListener("click", () => this.toggle());
  }
}

class Dataset extends APIObject {
  get title() {
    return this.api_data.entry_id;
  }
}
customElements.define("geospaas-dataset", Dataset);

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
  // let tags = document.getElementById("id_tags").value;
  // let keywords = document.getElementById("id_keywords").value;
  // let full_text = document.getElementById("id_full_text").value;
  // let parameters = document.getElementById("id_parameters").value;

  if(polygon) {full_request_parameters.location__intersects = polygon;}
  if(time_coverage_start) {full_request_parameters.time_coverage_end__gte = time_coverage_start;}
  if(time_coverage_end) {full_request_parameters.time_coverage_start__lte = time_coverage_end;}
  // if(tags) {full_request_parameters.tags = tags;}

  fetch(`${url}?` + new URLSearchParams(full_request_parameters).toString())
    .then(response => response.json())
    .then(page => display_page(page))
    .catch(error => console.log(`${error}: Failed to get datasets`));
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
  document.getElementById("datasets_page_size").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      document.getElementById("dataset_search_button").click();
    }
  });

// let footprints_layer_style = {
//     "color": "#0000ff",
//     "weight": 1,
//     "opacity": 0.9,
//     "fillOpacity": 0.1,
// };

// let polygons = {};
  // // highlights dataset coverage on the map
  // document.querySelectorAll(".dataset_row").forEach(
  //   function(element) {
  //     polygons[element.ajax_url] = new L.GeoJSON.AJAX(
  //       element.ajax_url,
  //       {style: footprints_layer_style}).addTo(window.maps[0]);
  //   }
  // );

  // $(".dataset_row").hover(
  //   function(){
  //     $(this).css("background-color", "#ffeeee");
  //     polygons[$(this).attr("ajax_url")].setStyle({color: '#ff0000'});
  //   },
  //   function(){
  //     $(this).css("background-color", "#ffffff");
  //     polygons[$(this).attr("ajax_url")].setStyle({color: '#0000ff'});
  //   },
  // );
});
