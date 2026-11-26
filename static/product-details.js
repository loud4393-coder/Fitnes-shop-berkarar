(() => {
  const $ = (selector, root=document) => root.querySelector(selector);
  const modal = $('#productModal');
  if (!modal || typeof PRODUCTS === 'undefined') return;

  let currentProduct = null;
  let chosenSize = '';
  let chosenColor = '';

  const moneyDetail = value => `${new Intl.NumberFormat('ru-RU',{maximumFractionDigits:0}).format(value)} TMT`;
  const sizesFor = product => {
    if (product.category === 'Кроссовки') return ['39','40','41','42','43','44'];
    if (product.category === 'Аксессуары' || product.category === 'Сумки') return ['One size'];
    return ['S','M','L','XL'];
  };

  function openDetails(product) {
    currentProduct = product;
    chosenSize = '';
    chosenColor = product.color || 'Основной цвет';
    $('#detailImage').src = product.image;
    $('#detailImage').alt = product.name;
    $('#detailCategory').textContent = product.category;
    $('#detailName').textContent = product.name;
    $('#detailPrice').textContent = moneyDetail(product.price);
    $('#detailDescription').textContent = product.description || 'Описание товара уточняется.';
    $('#detailQuantity').value = '1';
    $('#sizeHint').textContent = 'Выберите размер';
    $('#detailSizes').innerHTML = sizesFor(product).map(size =>
      `<button class="size-choice" type="button" data-size="${size}">${size}</button>`
    ).join('');
    $('#detailColors').innerHTML = `<button class="color-choice active" type="button" data-color="${String(chosenColor).replace(/"/g,'&quot;')}"><span class="color-dot"></span>${chosenColor}</button>`;
    $('#detailColorLabel').textContent = chosenColor;
    $('#detailSizes').querySelectorAll('[data-size]').forEach(button => {
      if (button.dataset.size === 'One size') {
        button.classList.add('active');
        chosenSize = 'One size';
      }
    });
    modal.classList.add('open');
    modal.setAttribute('aria-hidden','false');
    document.body.classList.add('locked');
  }

  function closeDetails() {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden','true');
    if (!$('#cartDrawer')?.classList.contains('open') && !$('#checkoutModal')?.classList.contains('open') &&
        !$('#menuDrawer')?.classList.contains('open')) document.body.classList.remove('locked');
  }

  // A card opens the product view; the small plus button keeps its quick-add behavior.
  $('#productGrid')?.addEventListener('click', event => {
    if (event.target.closest('[data-add]')) return;
    const card = event.target.closest('.product-card');
    if (!card) return;
    const index = [...$('#productGrid').querySelectorAll('.product-card')].indexOf(card);
    const visibleProducts = PRODUCTS.filter(product => {
      const active = $('#categoryTabs .active')?.dataset.category || 'Все';
      const query = ($('#productSearch')?.value || '').trim().toLocaleLowerCase('ru');
      return (active === 'Все' || product.category === active) &&
        (!query || `${product.name} ${product.category} ${product.color}`.toLocaleLowerCase('ru').includes(query));
    });
    if (visibleProducts[index]) openDetails(visibleProducts[index]);
  });

  $('#detailSizes').addEventListener('click', event => {
    const button = event.target.closest('[data-size]');
    if (!button) return;
    chosenSize = button.dataset.size;
    $('#detailSizes').querySelectorAll('[data-size]').forEach(item => item.classList.toggle('active', item === button));
    $('#sizeHint').textContent = `Выбран: ${chosenSize}`;
  });

  $('#detailColors').addEventListener('click', event => {
    const button = event.target.closest('[data-color]');
    if (!button) return;
    chosenColor = button.dataset.color;
    $('#detailColors').querySelectorAll('[data-color]').forEach(item => item.classList.toggle('active', item === button));
    $('#detailColorLabel').textContent = chosenColor;
  });

  $('#detailAdd').addEventListener('click', () => {
    if (!currentProduct) return;
    if (!chosenSize) {
      $('#sizeHint').textContent = 'Сначала выберите размер';
      $('#detailSizes').scrollIntoView({block:'nearest',behavior:'smooth'});
      return;
    }
    const quantity = Math.max(1, Math.min(5, Number($('#detailQuantity').value) || 1));
    const addButton = document.querySelector(`[data-add="${currentProduct.id}"]`);
    if (!addButton) return;
    // Existing demo cart is keyed by product ID. Store the selected variant alongside it.
    window.FITNESS_SELECTED_VARIANTS = window.FITNESS_SELECTED_VARIANTS || {};
    window.FITNESS_SELECTED_VARIANTS[currentProduct.id] = {size:chosenSize,color:chosenColor};
    for (let i=0;i<quantity;i++) addButton.click();
    closeDetails();
  });

  modal.querySelectorAll('[data-close-product]').forEach(button => button.addEventListener('click', closeDetails));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeDetails(); });

  // Reflect the selected variant in the existing cart UI without changing its core logic.
  const cartItems = $('#cartItems');
  if (cartItems) {
    const observer = new MutationObserver(() => {
      cartItems.querySelectorAll('.cart-row').forEach(row => {
        const remove = row.querySelector('[data-remove]');
        const id = remove?.dataset.remove;
        const variant = id && window.FITNESS_SELECTED_VARIANTS?.[id];
        const small = row.querySelector('small');
        if (variant && small && !small.dataset.variantShown) {
          small.textContent += ` · ${variant.size} · ${variant.color}`;
          small.dataset.variantShown = '1';
        }
      });
    });
    observer.observe(cartItems, {childList:true,subtree:true});
  }

  // Append the selected variants to the existing optional comment. The current
  // backend already forwards this field to Telegram, so no price/order API changes are needed.
  $('#checkoutForm')?.addEventListener('submit', () => {
    const comment = $('#checkoutForm [name="comment"]');
    if (!comment) return;
    const variants = Object.entries(window.FITNESS_SELECTED_VARIANTS || {})
      .filter(([id]) => typeof cart !== 'undefined' && Number(cart[id] || 0) > 0)
      .map(([id,variant]) => {
        const product = PRODUCTS.find(item => item.id === id);
        return product ? `${product.name}: ${variant.size}, ${variant.color}` : '';
      }).filter(Boolean);
    if (variants.length) {
      const prefix = comment.value.trim();
      const suffix = `Выбор: ${variants.join('; ')}`;
      comment.value = [prefix,suffix].filter(Boolean).join(' | ').slice(0,300);
    }
  }, true);
})();