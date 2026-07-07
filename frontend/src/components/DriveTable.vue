<template>
  <div class="table-responsive card border-0 shadow-sm">
    <table class="table mb-0">
      <thead>
        <tr>
          <th>Position</th>
          <th>Company</th>
          <th>Skills</th>
          <th>Deadline</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="drive in drives" :key="drive.id">
          <td><strong>{{ drive.title }}</strong><br><small>{{ drive.experience_required || "-" }}</small></td>
          <td>{{ drive.company }}</td>
          <td>{{ drive.skills_required || "-" }}</td>
          <td>{{ drive.deadline }}</td>
          <td><StatusBadge :value="drive.status" /></td>
          <td class="d-flex flex-wrap gap-1">
            <template v-if="admin">
              <button class="btn btn-success btn-sm" @click="$emit('action', drive, 'approve')">Approve</button>
              <button class="btn btn-warning btn-sm" @click="$emit('action', drive, 'reject')">Reject</button>
              <button class="btn btn-danger btn-sm" @click="$emit('action', drive, 'delete')">Remove</button>
            </template>
            <template v-if="company">
              <button class="btn btn-outline-primary btn-sm" @click="$emit('edit', drive)">Edit</button>
              <button class="btn btn-outline-danger btn-sm" @click="$emit('action', drive, 'close')">Close</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import StatusBadge from "./StatusBadge.vue";

export default {
  name: "DriveTable",
  components: { StatusBadge },
  props: {
    drives: { type: Array, default: () => [] },
    admin: { type: Boolean, default: false },
    company: { type: Boolean, default: false },
  },
  emits: ["edit", "action"],
};
</script>
