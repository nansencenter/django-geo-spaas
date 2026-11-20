import {APIObjectElement} from "/static/base_viewer/js/geospaas_api.js"

document.addEventListener("DOMContentLoaded", function() {
    let host = `${window.location.protocol}//${window.location.host}`;
    fetch(`${host}/harvesting/api/providers/`)
        .then(response => response.json())
        .then(page => {
            let selector = document.getElementById("providers_selector");
            for(let provider_json of page.results) {
                let option = document.createElement("option");
                option.value = provider_json.id;
                option.text = provider_json.name;
                selector.add(option);
            }
        })
        .catch(error => console.log(`${error}: Failed to get providers`));
});