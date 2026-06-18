import { execSync } from 'child_process';

const CLI = 'cd /home/sandbox/apps/trip-hub && PYTHONPATH=src python3 src/cli.py';

export function load() {
	try {
		const out = execSync(`${CLI} catalog`, { encoding: 'utf-8', timeout: 10000 });
		const items = JSON.parse(out);
		return { items };
	} catch {
		return { items: [] };
	}
}
