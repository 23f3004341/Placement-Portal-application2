<template>
  <section class="row g-3">
    <div class="col-lg-8">
      <form class="card border-0 shadow-sm" @submit.prevent="$emit('screen')">
        <div class="card-body p-4">
          <h1 class="h3">ATS-style Resume Screener</h1>
          <p class="text-secondary">Keyword guidance only, not an automated hiring decision.</p>
          <label class="form-label">Resume text</label>
          <textarea
            class="form-control mb-3"
            rows="10"
            maxlength="50000"
            :value="resumeText"
            required
            @input="$emit('update:resumeText', $event.target.value)"
          />
          <label class="form-label">Job description</label>
          <textarea
            class="form-control mb-3"
            rows="8"
            maxlength="30000"
            :value="jobDescription"
            required
            @input="$emit('update:jobDescription', $event.target.value)"
          />
          <button class="btn btn-primary">Screen resume</button>
        </div>
      </form>
    </div>
    <div class="col-lg-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-body p-4">
          <template v-if="result">
            <div class="display-4 fw-bold text-primary">{{ result.score }}%</div>
            <h2 class="h5">{{ result.summary }}</h2>
            <hr>
            <h3 class="h6 text-success">Matched</h3>
            <span v-for="term in result.matched" :key="term" class="badge text-bg-success me-1 mb-1">
              {{ term }}
            </span>
            <h3 class="h6 text-danger mt-3">Missing</h3>
            <span v-for="term in result.missing" :key="term" class="badge text-bg-light border me-1 mb-1">
              {{ term }}
            </span>
          </template>
          <p v-else class="text-secondary">Your analysis will appear here.</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "AtsScreener",
  props: {
    resumeText: { type: String, default: "" },
    jobDescription: { type: String, default: "" },
    result: { type: Object, default: null },
  },
  emits: ["screen", "update:resumeText", "update:jobDescription"],
};
</script>
