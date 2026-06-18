import { execSync } from 'child_process';

const CLI = 'cd /home/sandbox/apps/trip-hub && PYTHONPATH=src python3 src/cli.py';

export function load({ params }) {
	try {
		const out = execSync(`${CLI} trip ${params.id}`, { encoding: 'utf-8', timeout: 10000 });
		const trip = JSON.parse(out);
		return { trip };
	} catch {
		return { trip: null };
	}
}
