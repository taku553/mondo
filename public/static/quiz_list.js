// ホーム画面のクイズ一覧：並び替え（作成日）・タグ絞り込み・ページ送り（1ページ14件）
(function () {
  const PAGE_SIZE = 14;
  const grid = document.querySelector('.grid');
  if (!grid) return;

  const sortSelect = document.getElementById('quiz-sort');
  const searchBox = document.querySelector('.search-box');
  const pagination = document.getElementById('quiz-pagination');
  const cards = Array.from(grid.querySelectorAll('.card'));
  let currentPage = 1;

  const createdTime = card => Date.parse(card.dataset.createdAt) || 0;

  function sortCards() {
    const direction = sortSelect.value === 'oldest' ? 1 : -1;
    cards.sort((a, b) => direction * (createdTime(a) - createdTime(b)));
    cards.forEach(card => grid.appendChild(card));
  }

  function matchesTag(card, term) {
    if (term === '') return true;
    return Array.from(card.querySelectorAll('.tag'))
      .some(tag => tag.textContent.toLowerCase().trim().includes(term));
  }

  function renderPagination(pageCount) {
    pagination.innerHTML = '';
    if (pageCount <= 1) return;
    for (let page = 1; page <= pageCount; page++) {
      const button = document.createElement('button');
      button.textContent = page;
      button.classList.toggle('active', page === currentPage);
      button.addEventListener('click', () => {
        currentPage = page;
        render();
      });
      pagination.appendChild(button);
    }
  }

  function render() {
    const term = searchBox ? searchBox.value.toLowerCase().trim() : '';
    const matches = cards.filter(card => matchesTag(card, term));
    const pageCount = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
    currentPage = Math.min(currentPage, pageCount);

    cards.forEach(card => { card.style.display = 'none'; });
    matches
      .slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
      .forEach(card => { card.style.display = ''; });
    renderPagination(pageCount);
  }

  sortSelect.addEventListener('change', () => {
    currentPage = 1;
    sortCards();
    render();
  });

  if (searchBox) {
    searchBox.addEventListener('input', () => {
      currentPage = 1;
      render();
    });
  }

  sortCards();
  render();
})();
