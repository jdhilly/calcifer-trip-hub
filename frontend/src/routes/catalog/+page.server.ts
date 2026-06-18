import { cli, cliAction } from '$lib/cli.js';
import { fail } from '@sveltejs/kit';

export function load() {
	const items = cli('catalog');
	return { items: items ?? [] };
}

export const actions = {
	update: async ({ request }) => {
		const fd = await request.formData();
		const itemId = fd.get('itemId');
		if (!itemId) return fail(400, { error: 'Missing itemId' });
		const name = fd.get('name');
		const category = fd.get('category');
		const qty = fd.get('default_quantity');
		const args = ['catalog-update', String(itemId)];
		if (name) args.push('--name', String(name));
		if (category !== null) args.push('--category', String(category));
		if (qty) args.push('--default-quantity', String(qty));
		return cliAction(...args);
	},

	remove: async ({ request }) => {
		const fd = await request.formData();
		const itemId = fd.get('itemId');
		if (!itemId) return fail(400, { error: 'Missing itemId' });
		return cliAction('catalog-remove', String(itemId));
	}
};
