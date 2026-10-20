/* Optional in-game Council tab. Requires game-issued short-lived player token.
 * Never place the signing key or a server-role assertion in the browser.
 */
export function mountWardensCouncil(root, { baseUrl, room, getPlayerToken }) {
  const api = baseUrl.replace(/\/$/, '') + '/v1/rooms/' + encodeURIComponent(room);
  const box = (tag, label, parent, attrs = {}) => {
    const el = document.createElement(tag);
    if (label != null) el.textContent = String(label); // never inject player HTML
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
    parent.append(el);
    return el;
  };
  async function call(path, method = 'GET', payload) {
    const token = await getPlayerToken();
    const res = await fetch(api + path, {
      method,
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      ...(payload === undefined ? {} : { body: JSON.stringify(payload) })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'HTTP ' + res.status);
    return data;
  }
  box('h2', 'Council of Wardens', root);
  box('p', 'Propose changes. Discuss. Vote. New room rules start at a safe checkpoint.', root);
  const status = box('p', '', root, { role: 'status', 'aria-live': 'polite' });
  const form = box('form', null, root);
  const kind = box('select', null, form, { 'aria-label': 'Suggestion type' });
  for (const name of ['gameplay', 'design', 'lore', 'code']) box('option', name, kind, { value: name });
  const nameInput = box('input', null, form, { placeholder: 'Proposal title', required: '', minlength: '5', maxlength: '100' });
  const detailInput = box('textarea', null, form, { placeholder: 'Describe your proposal', required: '', maxlength: '2000' });
  const rule = box('select', null, form, { 'aria-label': 'Room rule proposal' });
  for (const [value, label] of [['hints_enabled', 'Enable hints'], ['turn_timer_seconds', '90-second turns']])
    box('option', label, rule, { value });
  const setVisibility = () => { rule.hidden = kind.value !== 'gameplay'; };
  kind.addEventListener('change', setVisibility);
  setVisibility();
  box('button', 'Submit suggestion', form, { type: 'submit' });
  const items = box('section', null, root, { 'aria-label': 'Council proposals' });
  async function refresh() {
    items.replaceChildren();
    const proposals = await call('/proposals');
    for (const p of proposals) {
      const article = box('article', null, items);
      box('h3', p.title + ' — ' + p.status, article);
      box('p', p.kind + ': ' + p.detail, article);
      const action = async (path, data) => {
        try {
          await call('/proposals/' + p.id + '/' + path, 'POST', data);
          status.textContent = 'Council record updated.';
          await refresh();
        } catch (err) { status.textContent = err.message; }
      };
      if (p.status === 'draft') box('button', 'Open ballot', article).onclick = () => action('open');
      if (p.status === 'voting') {
        box('button', 'Vote yes', article).onclick = () => action('vote', { choice: 'yes' });
        box('button', 'Vote no', article).onclick = () => action('vote', { choice: 'no' });
        box('button', 'Close when ready', article).onclick = () => action('close');
      }
      const discuss = box('details', null, article);
      box('summary', 'Discussion', discuss);
      const comments = box('div', null, discuss);
      const commentForm = box('form', null, discuss);
      const commentInput = box('input', null, commentForm, { maxlength: '1000', placeholder: 'Offer evidence or an objection' });
      box('button', 'Post comment', commentForm, { type: 'submit' });
      const loadComments = async () => {
        comments.replaceChildren();
        const list = await call('/proposals/' + p.id + '/comments');
        for (const c of list) box('p', c.author + ': ' + c.body, comments);
      };
      discuss.addEventListener('toggle', () => {
        if (discuss.open) loadComments().catch(err => { status.textContent = err.message; });
      });
      commentForm.addEventListener('submit', async event => {
        event.preventDefault();
        try {
          await call('/proposals/' + p.id + '/comments', 'POST', { body: commentInput.value });
          commentInput.value = '';
          await loadComments();
        } catch (err) { status.textContent = err.message; }
      });
    }
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const change = kind.value !== 'gameplay' ? undefined :
      rule.value === 'hints_enabled' ? { hints_enabled: true } : { turn_timer_seconds: 90 };
    try {
      await call('/proposals', 'POST', {
        kind: kind.value, title: nameInput.value, detail: detailInput.value,
        ...(change ? { change } : {})
      });
      nameInput.value = ''; detailInput.value = '';
      status.textContent = 'Proposal added.';
      await refresh();
    } catch (err) { status.textContent = err.message; }
  });
  refresh().catch(err => { status.textContent = err.message; });
  return { refresh, destroy() { root.replaceChildren(); } };
}
