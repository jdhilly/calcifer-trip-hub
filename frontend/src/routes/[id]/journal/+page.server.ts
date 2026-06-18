import { cli, cliAction } from '$lib/cli.js';
import { fail } from '@sveltejs/kit';

export function load({ params }) {
	const trip = cli('trip', params.id);
	const entries = cli('journal', params.id);
	return {
		trip,
		entries: entries ?? []
	};
}

export const actions = {
	add: async ({ request, params }) => {
		const fd = await request.formData();
		const content = fd.get('content')?.toString().trim();
		if (!content) return fail(400, { error: 'Missing content' });
		const date = fd.get('date')?.toString().trim() || new Date().toISOString().slice(0, 10);
		const author = fd.get('author')?.toString().trim() || '';
		return cliAction('journal-add', params.id, '--date', date, '--content', content, '--author', author);
	},

	delete: async ({ request }) => {
		const fd = await request.formData();
		const entryId = fd.get('entryId');
		if (!entryId) return fail(400, { error: 'Missing entryId' });
		return cliAction('journal-delete', String(entryId));
	}
};
