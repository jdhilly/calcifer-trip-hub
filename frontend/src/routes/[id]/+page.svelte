<script lang="ts">
	import { PageHeader } from '@calcifer/ui';
	import { ArrowRight, ListChecks, Users, FileText, BookOpen, Luggage, Check } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let items = $derived(trip.items ?? []);
	let artifacts = $derived(trip.artifacts ?? []);

	function formatDate(d: string): string {
		return new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
	}

	let total = $derived(items.reduce((s: number, i: any) => s + (i.quantity || 1), 0));
	let depart = $derived(items.reduce((s: number, i: any) => s + (i.checked || 0), 0));
	let pct = $derived(total > 0 ? Math.round((depart / total) * 100) : 0);

	const navCards = [
		{ href: 'checklist', icon: ListChecks, title: 'Checklist', desc: `${depart}/${total}` },
		{ href: 'participants', icon: Users, title: 'Participants', desc: 'Timeline de présence' },
		{ href: 'briefing', icon: FileText, title: 'Briefing', desc: `${artifacts.length} artifact(s)` },
		{ href: 'journal', icon: BookOpen, title: 'Journal', desc: 'Carnet de bord' },
	];
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader
		title={trip?.destination ?? 'Introuvable'}
		backHref="/"
		description={trip ? `${formatDate(trip.start_date)} → ${formatDate(trip.end_date)}` : ''}
	/>

	{#if trip}
		<div class="mb-6">
			<div class="flex items-center justify-between text-xs text-coal-400">
				<span><Luggage size={14} class="inline" /> Préparation</span>
				<span>{depart}/{total} ({pct}%)</span>
			</div>
			<div class="mt-1 h-2 w-full rounded-full bg-coal-800">
				<div class="h-2 rounded-full bg-ember-500 transition-all" style="width: {pct}%"></div>
			</div>
		</div>

		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			{#each navCards as c}
				<a href={`/${trip.id}/${c.href}`} class="group block">
					<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-ember-500/45 hover:bg-coal-900/70">
						<div class="flex items-center gap-3">
							<c.icon size={24} class="text-ember-400" />
							<div>
								<h3 class="font-semibold text-coal-50">{c.title}</h3>
								<p class="text-sm text-coal-400">{c.desc}</p>
							</div>
						</div>
					</div>
				</a>
			{/each}
		</div>

		{#if items.length > 0}
			<h2 class="mb-3 mt-8 font-display text-lg text-coal-300">Articles dans la checklist</h2>
			<div class="space-y-2">
				{#each items.slice(0, 10) as item}
					<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-3">
						<div class="flex items-center gap-3">
							{#if item.checked}
								<Check size={18} class="text-ember-400" />
							{:else}
								<span class="inline-block h-[18px] w-[18px] rounded border-2 border-coal-600"></span>
							{/if}
							<div>
								<p class={['text-sm', item.checked ? 'text-coal-500 line-through' : 'text-coal-100']}>{item.label}</p>
								<p class="text-xs text-coal-500">{item.category}</p>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>
