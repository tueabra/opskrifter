let search_data = undefined;
async function fetch_data() {
  await fetch(`${SITEURL}/search-data.json`)
    .then(response => response.json())
    .then(data => search_data = data)
    .catch(error => alert(error));
}

function tokenize(input) {
    const output = [];
    input.trim().toLowerCase().split(' ').forEach(token => {
        if(token !== "") {
            output.push(token);
        }
    });
    return output;
}

function search(tokens) {
    const results = [];
    search_data.forEach(result => {
        let isAllFound = true;
        tokens.forEach(token => {
            let isFound = false;
            result["tokens"].forEach(word => {
                if(word.indexOf(token) !== -1) {
                    isFound = true;
                }
            });
            isAllFound = isAllFound && isFound;
        });
        if(isAllFound) {
            results.push(result)
        }
    });
    return results;
}

const searchbox = document.getElementById("search-box");
const searchresults = document.getElementById("search-results");

function hide_search() {
    searchresults.style.display = 'none';
}

function show_search() {
    searchresults.style.display = 'block';
}

function populate_search(results) {
    if(results.length === 0) {
        searchresults.innerHTML = "<li><i>Ingen resultater</i></li>";
        return;
    }
    searchresults.innerHTML = results.map(result => {
        return `<li><a href="${SITEURL}${result.url}">${result.name}</a></li>`;
    }).join('');
}


searchbox.addEventListener('keyup', async () => {

    if(search_data === undefined) {
        await fetch_data();
    }

    if(search_data === undefined) {
        alert("Something went wrong!");
        return;
    }

    const tokens = tokenize(searchbox.value);
    if(tokens.length === 0) {
        hide_search();
        return;
    }

    const results = search(tokens);
    populate_search(results);
    show_search();
});
