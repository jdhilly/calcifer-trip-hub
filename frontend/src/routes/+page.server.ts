import { execSync } from 'child_process';

const CLI = 'cd /home/sandbox/apps/trip-hub && PYTHONPATH=src python3 src/cli.py';

export function load() {
	try {
		const out = execSync(`${CLI} trips`, { encoding: 'utf-8', timeout: 10000 });
		const trips = JSON.parse(out);
		return { trips };
	} catch {
		return { trips: [] };
	}
}
