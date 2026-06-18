<script lang="ts">
	import { PageHeader } from '@calcifer/ui';
	import { Calendar, ArrowRight, Check, X, Compass, ArrowUp, RotateCw } from '@lucide/svelte/icons';

	let { data } = $props();
	let trips = $state(data.trips);
	let online = $state(typeof navigator !== 'undefined' ? navigator.onLine : true);

	let upcoming = $derived.by(() => {
		const now = new Date();
		const inFourWeeks = new Date();
		inFourWeeks.setDate(inFourWeeks.getDate() + 30);
		const active = trips.filter(
			(t: any) => new Date(t.start_date) <= inFourWeeks && new Date(t.end_date) >= now
		);
		return active.length > 0 ? active[0] : (trips.length > 0 ? trips[0] : null);
	});

	function formatDate(d: string): string {
		return new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
	}

	function isOngoing(t: any): boolean {
		const now = new Date();
		return new Date(t.start_date) <= now && new Date(t.end_date) >= now;
	}

	function isFuture(t: any): boolean {
		return new Date(t.start_date) > new Date();
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title="Voyages" description="Préparez vos valises et ne rien oublier" />

	{#if trips.length === 0}
		<div class="mt-6 rounded-2xl border border-coal-800 bg-coal-900/55 p-8 text-center">
			<p class="text-coal-400">Aucun voyage pour l'instant.</p>
		</div>
	{:else}
		{#if upcoming}
			<div class="mt-6">
				<h2 class="font-display text-xl text-ember-500">
					{#if isOngoing(upcoming)}
						<RotateCw size={18} class="inline" /> En cours
					{:else}
						<ArrowUp size={18} class="inline" /> Prochain voyage
					{/if}
				</h2>

				<a href={`/${upcoming.id}`} class="group mt-2 block">
					<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-ember-500/45 hover:bg-coal-900/70">
						<div class="flex items-center gap-3">
							<span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-ember-500/10 text-ember-300 ring-1 ring-ember-500/20 transition-all duration-300 group-hover:scale-105 group-hover:ring-ember-500/40">
								<Calendar size={20} />
							</span>
							<div class="flex-1">
								<h3 class="font-semibold text-coal-50">{upcoming.destination}</h3>
								<p class="text-sm text-coal-400">
									{formatDate(upcoming.start_date)}
									<ArrowRight size={14} class="inline" />
									{formatDate(upcoming.end_date)}
								</p>
							</div>
						</div>
					</div>
				</a>
			</div>
		{/if}

		<div class="mt-8">
			<h2 class="font-display text-lg text-coal-300">Tous les voyages</h2>
			<div class="mt-3 space-y-3">
				{#each trips as trip}
					<a href={`/${trip.id}`} class="group block">
						<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-ember-500/45 hover:bg-coal-900/70">
							<div class="flex items-start gap-3">
								<div class="flex-1">
									<h3 class="font-semibold text-coal-50">{trip.destination}</h3>
									<p class="text-sm text-coal-400">
										{formatDate(trip.start_date)}
										<ArrowRight size={14} class="inline" />
										{formatDate(trip.end_date)}
									</p>
								</div>
								<div class="flex items-center gap-2 text-xs">
									{#if isOngoing(trip)}
										<span class="flex items-center gap-1 text-ember-500"><Check size={14} /> En cours</span>
									{:else if isFuture(trip)}
										<span class="flex items-center gap-1 text-ember-400"><Calendar size={14} /> À venir</span>
									{:else}
										<span class="flex items-center gap-1 text-coal-500"><X size={14} /> Terminé</span>
									{/if}
								</div>
							</div>
						</div>
					</a>
				{/each}
			</div>
		</div>
	{/if}
</div>
