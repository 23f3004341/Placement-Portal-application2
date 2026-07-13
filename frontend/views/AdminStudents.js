window.AdminStudentsView = `
      <section v-else-if="page === 'admin-students'">
        <list-header
          title="Students"
          placeholder="Search name, ID, or contact"
          v-model="search"
          :button-class="themeButtonClass"
          :eyebrow-class="themeTextClass"
          @search="loadAdminStudents"
        ></list-header>
        <div class="table-responsive card shadow-sm border-0">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>Student</th>
                <th>Student ID</th>
                <th>Course</th>
                <th>Contact</th>
                <th>Account</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!students.length"><td colspan="6" class="text-center text-secondary py-5">No students found.</td></tr>
              <template v-for="s in students" :key="s.id">
              <tr>
                <td>{{ s.user.name }}</td>
                <td>{{ s.roll_number }}</td>
                <td>{{ s.course }} / {{ s.branch }}</td>
                <td>{{ s.user.contact }}</td>
                <td>
                  <status-badge :value="s.user.active ? 'active' : 'inactive'"></status-badge>
                </td>
                <td class="d-flex flex-wrap gap-1">
                  <button
                    class="btn btn-sm"
                    :class="themeOutlineButtonClass"
                    @click="startStudentEdit(s)"
                  >
                    Edit</button
                  >
                  <button
                    class="btn btn-outline-warning btn-sm"
                    @click="
                      adminStatus(
                        'students',
                        s.id,
                        s.user.active ? 'blacklist' : 'unblacklist'
                      )
                    "
                  >
                    {{ s.user.active ? "Blacklist" : "Unblacklist" }}</button
                  ><button
                    class="btn btn-danger btn-sm"
                    @click="adminDelete('students', s.id)"
                  >
                    Delete
                  </button>
                </td>
              </tr>
              <tr v-if="editingStudentId === s.id" class="table-light">
                <td colspan="6">
                  <form class="row g-2 align-items-end" @submit.prevent="saveStudentEdit">
                    <div class="col-md-3">
                      <label class="form-label small">Name</label>
                      <input class="form-control form-control-sm" v-model.trim="studentEditForm.name" />
                    </div>
                    <div class="col-md-3">
                      <label class="form-label small">Email</label>
                      <input class="form-control form-control-sm" type="email" v-model.trim="studentEditForm.email" />
                    </div>
                    <div class="col-md-2">
                      <label class="form-label small">Contact</label>
                      <input class="form-control form-control-sm" v-model="studentEditForm.contact" @input="digitsOnly(studentEditForm, 'contact', 10)" />
                    </div>
                    <div class="col-md-2">
                      <label class="form-label small">Student ID</label>
                      <input class="form-control form-control-sm" v-model.trim="studentEditForm.roll_number" />
                    </div>
                    <div class="col-md-2">
                      <label class="form-label small">Year</label>
                      <input class="form-control form-control-sm" type="number" v-model="studentEditForm.graduation_year" />
                    </div>
                    <div class="col-md-3">
                      <label class="form-label small">Course</label>
                      <input class="form-control form-control-sm" v-model.trim="studentEditForm.course" />
                    </div>
                    <div class="col-md-3">
                      <label class="form-label small">Branch</label>
                      <input class="form-control form-control-sm" v-model.trim="studentEditForm.branch" />
                    </div>
                    <div class="col-md-2">
                      <label class="form-label small">CGPA</label>
                      <input class="form-control form-control-sm" type="number" step="0.01" v-model="studentEditForm.cgpa" />
                    </div>
                    <div class="col-md-4 d-flex gap-2">
                      <button class="btn btn-sm" :class="themeButtonClass" type="submit">Save</button>
                      <button class="btn btn-outline-secondary btn-sm" type="button" @click="cancelStudentEdit">Cancel</button>
                    </div>
                  </form>
                </td>
              </tr>
              </template>
            </tbody>
          </table>
        </div>
      </section>
`;
