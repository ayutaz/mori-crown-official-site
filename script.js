const chips = document.querySelectorAll(".chip");
const newsCards = document.querySelectorAll(".news-card");

function applyNewsFilter(filter) {
  newsCards.forEach((card) => {
    const category = card.dataset.category;
    const visible = filter === "all" || category === filter;
    card.classList.toggle("is-hidden", !visible);
  });
}

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    const filter = chip.dataset.filter;
    chips.forEach((target) => target.classList.remove("is-active"));
    chip.classList.add("is-active");
    applyNewsFilter(filter);
  });
});
