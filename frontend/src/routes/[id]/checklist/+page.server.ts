import { cli, cliAction } from '$lib/cli.js';
import { fail } from '@sveltejs/kit';

export function load({ params }) {
	const trip = cli('trip', params.id);
	const catalog = cli('catalog');
	return {
		trip: trip ?? { id: params.id, destination: 'Voyage', items: [] },
		catalog: catalog ?? []
	};
}

export const actions = {
	toggle: async ({ request }) => {
		const fd = await request.formData();
		const itemId = fd.get('itemId');
		const checked = fd.get('checked');
		if (!itemId) return fail(400, { error: 'Missing itemId' });
		const args = ['list-toggle', String(itemId)];
		if (checked) args.push('--checked', String(checked));
		return cliAction(...args);
	},

	add: async ({ request, params }) => {
		const fd = await request.formData();
		const label = fd.get('label')?.toString().trim();
		if (!label) return fail(400, { error: 'Missing label' });
		return cliAction(
			'list-add', params.id,
			'--label', label,
			'--category', (fd.get('category')?.toString() ?? '').trim(),
			'--quantity', fd.get('quantity')?.toString() ?? '1'
		);
	},

	remove: async ({ request }) => {
		const fd = await request.formData();
		const itemId = fd.get('itemId');
		if (!itemId) return fail(400, { error: 'Missing itemId' });
		return cliAction('list-remove', String(itemId));
	},

	import: async ({ request, params }) => {
		const fd = await request.formData();
		const raw = fd.get('items');
		if (!raw) return fail(400, { error: 'Missing items' });
		const b64 = Buffer.from(raw.toString()).toString('base64');
		return cliAction('list-import', params.id, b64);
	},

	update: async ({ request }) => {
		const fd = await request.formData();
		const itemId = fd.get('itemId');
		const quantity = fd.get('quantity');
		if (!itemId || !quantity) return fail(400, { error: 'Missing itemId or quantity' });
		return cliAction('list-update', String(itemId), '--quantity', String(quantity));
	},
};
