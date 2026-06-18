import { cli, cliAction } from '$lib/cli.js';
import { fail } from '@sveltejs/kit';

export function load({ params }) {
	const trip = cli('trip', params.id);
	const artifacts = cli('artifacts', params.id);
	return {
		trip,
		artifacts: artifacts ?? []
	};
}

export const actions = {
	generate: async ({ request, params }) => {
		const fd = await request.formData();
		const type = fd.get('type')?.toString();
		if (!type) return fail(400, { error: 'Missing artifact type' });

		// Map trip ID to notebook key
		const tripKey = params.id === 'legacy-1' ? 'lauris' : params.id;
		
		const result = cliAction('notebooklm-generate', tripKey, type);
		return result;
	}
};
