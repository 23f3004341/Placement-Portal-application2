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
        <div v-if="selectedAdminStudent" class="card border-0 shadow-sm mb-4">
          <div class="card-body p-4">
            <div class="d-flex justify-content-between gap-3 mb-4"><div><p class="small text-uppercase text-secondary fw-semibold mb-1">Student profile</p><h2 class="h4 mb-1">{{ selectedAdminStudent.user.name }}</h2><status-badge :value="selectedAdminStudent.user.active ? 'active' : 'inactive'"></status-badge></div><button class="btn btn-outline-secondary btn-sm align-self-start" @click="selectedAdminStudent = null">Back to list</button></div>
            <div class="row g-4"><div class="col-md-6"><h3 class="h6 text-secondary text-uppercase">Academic details</h3><dl class="row mb-0"><dt class="col-5">Student ID</dt><dd class="col-7">{{ selectedAdminStudent.roll_number }}</dd><dt class="col-5">Course</dt><dd class="col-7">{{ selectedAdminStudent.course || '-' }}</dd><dt class="col-5">Branch</dt><dd class="col-7">{{ selectedAdminStudent.branch || '-' }}</dd><dt class="col-5">Graduation year</dt><dd class="col-7">{{ selectedAdminStudent.graduation_year || '-' }}</dd><dt class="col-5">CGPA</dt><dd class="col-7">{{ selectedAdminStudent.cgpa ?? '-' }}</dd></dl></div><div class="col-md-6"><h3 class="h6 text-secondary text-uppercase">Contact details</h3><dl class="row mb-0"><dt class="col-4">Email</dt><dd class="col-8 text-break">{{ selectedAdminStudent.user.email }}</dd><dt class="col-4">Phone</dt><dd class="col-8">{{ selectedAdminStudent.user.contact || '-' }}</dd><dt class="col-4">Address</dt><dd class="col-8">{{ selectedAdminStudent.user.address || '-' }}</dd></dl></div></div>
          </div>
        </div>
        <div class="table-responsive card shadow-sm border-0 rounded-4 overflow-hidden">
          <table class="table table-hover align-middle mb-0">
            <thead>
              <tr>
                <th class="p-3">Student</th>
                <th class="p-3">Student ID</th>
                <th class="p-3">Course</th>
                <th class="p-3">Contact</th>
                <th class="p-3">Account</th>
                <th class="p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!students.length"><td colspan="6" class="text-center text-secondary py-5">No students found.</td></tr>
              <template v-for="s in students" :key="s.id">
              <tr>
                <td class="p-3"><a href="#" class="link-dark fw-semibold" @click.prevent="viewAdminStudent(s)">{{ s.user.name }}</a></td>
                <td class="p-3">{{ s.roll_number }}</td>
                <td class="p-3">{{ s.course }} / {{ s.branch }}</td>
                <td class="p-3">{{ s.user.contact }}</td>
                <td class="p-3">
                  <status-badge :value="s.user.active ? 'active' : 'inactive'"></status-badge>
                </td>
                <td class="p-3 d-flex flex-wrap gap-1">
                  <button
                    class="btn btn-sm btn-outline-secondary"
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
                    class="btn btn-outline-danger btn-sm"
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
                      <input class="form-control form-control-sm" :value="studentEditForm.roll_number" readonly />
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
