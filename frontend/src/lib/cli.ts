import { execSync } from 'child_process';

const CLI_BASE = 'cd /home/sandbox/apps/trip-hub && PYTHONPATH=src python3 src/cli.py';

export function cli(...args: string[]): any {
	try {
		const out = execSync(`${CLI_BASE} ${args.join(' ')}`, {
			encoding: 'utf-8',
			timeout: 10000
		});
		return JSON.parse(out);
	} catch (e: any) {
		if (e.stderr?.includes('usage:')) return null;
		throw e;
	}
}

export function cliAction(...args: string[]): { ok: boolean; error?: string; [key: string]: any } {
	try {
		const out = execSync(`${CLI_BASE} ${args.join(' ')}`, {
			encoding: 'utf-8',
			timeout: 10000
		});
		return JSON.parse(out);
	} catch (e: any) {
		return { ok: false, error: e.stderr?.toString()?.slice(0, 200) ?? 'Unknown error' };
	}
}
