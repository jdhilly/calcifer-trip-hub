import { cli, cliAction } from '$lib/cli.js';
import { fail } from '@sveltejs/kit';

export function load({ params }) {
	const trip = cli('trip', params.id);
	let participants: any[] = [];
	if (trip?.participants) {
		try { participants = JSON.parse(trip.participants); } catch {}
	}
	return { trip, participants };
}

export const actions = {
	update: async ({ request, params }) => {
		const fd = await request.formData();
		const raw = fd.get('participants');
		if (!raw) return fail(400, { error: 'Missing participants data' });
		// Validate JSON
		try { JSON.parse(raw.toString()); } catch {
			return fail(400, { error: 'Invalid JSON' });
		}
		return cliAction('participants-update', params.id, raw.toString());
	}
};
