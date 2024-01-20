

document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    loadBuddhaNames();
    
    document.getElementById('search-box').addEventListener('input', searchNames);
});

function loadCategories() {
    fetch('categories.json').then(response => response.json()).then(data => displayCategories(data));
}


function displayCategories(categories) {
    const container = document.getElementById('categories-container');
    // Populate categories
    categories.forEach(category => {
        // create a checkbox for each category
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = category.name;
        checkbox.id = category.name;
        checkbox.checked = true; 
        
        checkbox.addEventListener('change', function() {
            console.log(`Checkbox for ${category.name} changed to ${this.checked}`);

            searchNames(null);
        })
        
        const label = document.createElement('label');
        label.htmlFor = category.name;
        label.textContent = `${category.name} (${category.count})`;

        container.appendChild(checkbox);
        container.appendChild(label);
    });
}

function searchNames(event) {
    const container = document.getElementById('names-container');
    container.innerHTML = ''; // Clear existing content

    const searchTerm = document.getElementById('search-box').value.toLowerCase();
    // Implement search functionality

    fetch('categories.json').then(response => response.json()).then(data => {

        data.forEach(category => {
            // get the checkbox named with category name and its checked status
            const checkbox = document.getElementById(category.name);
            const isChecked = checkbox.checked;

            if (!isChecked) {
                return;
            }

            fetch(category.file)
                .then(response => response.json())
                .then(jj => filterAndDisplayNames(jj, searchTerm))
                .catch(error => console.error('Error loading Buddha names:', error));
        });
    });

    // fetch('book-buddha-names.json')
    //     .then(response => response.json())
    //     .then(jj => filterAndDisplayNames(jj, searchTerm))
    //     .catch(error => console.error("Error when searching:", error));
}

function filterAndDisplayNames(jj, searchTerm) {
    const container = document.getElementById('names-container');

    // if (searchTerm === '') {
    //     loadBuddhaNames();
    //     return;
    // }

    console.log('searchTerm: ' + searchTerm);

    const filteredNames = jj.names.filter(name => name.includes(searchTerm));

    if (filteredNames.length === 0) {
        // container.textContent = 'No names found.';
        // console.log('No names found.');
        return;
    }

    filteredNames.forEach(name => {
        const div = document.createElement('div');
        div.className = 'buddha-name';
        div.textContent = name;
        container.appendChild(div);
    });
}


function loadBuddhaNames() {
    fetch('categories.json').then(response => response.json()).then(data => {

        data.forEach(category => {
            fetch(category.file)
                .then(response => response.json())
                .then(jj => displayBuddhaNames(jj))
                .catch(error => console.error('Error loading Buddha names:', error));
        });
    });

    
}

function displayBuddhaNames(jj) {
    const container = document.getElementById('names-container');
    //container.innerHTML = ''; // Clear existing content

    jj.names.forEach(name => {
        const div = document.createElement('div');
        div.className = 'buddha-name';
        div.textContent = name;
        container.appendChild(div);
    });
}

