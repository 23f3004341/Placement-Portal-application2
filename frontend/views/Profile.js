window.ProfileView = `
      <section
        v-else-if="page === 'profile'"
        class="row justify-content-center"
      >
        <div class="col-xl-9">
          <form
            v-if="user && user.role === 'student'"
            class="card border-0 shadow-sm"
            @submit.prevent="saveStudentProfile"
          >
            <div class="card-body p-4">
              <h1 class="h3">Student Profile</h1>
              <div class="row g-3">
                <div class="col-md-4">
                  <label class="form-label"
                    >First name <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentProfile.user.first_name"
                    minlength="2"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">Middle name</label
                  ><input
                    class="form-control"
                    v-model.trim="studentProfile.user.middle_name"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Last name <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentProfile.user.last_name"
                    minlength="1"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label"
                    >Email <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="email"
                    v-model.trim="studentProfile.user.email"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label"
                    >Contact <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    inputmode="numeric"
                    pattern="[0-9]{10}"
                    maxlength="10"
                    v-model="studentProfile.user.contact"
                    @input="digitsOnly(studentProfile.user, 'contact', 10)"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Gender <span class="text-danger">*</span></label
                  ><select
                    class="form-select"
                    v-model="studentProfile.user.gender"
                    required
                  >
                    <option value="">Select gender</option>
                    <option
                      v-for="gender in genderOptions"
                      :key="gender"
                      :value="gender"
                    >
                      {{ gender }}
                    </option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Date of birth <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="date"
                    v-model="studentProfile.user.dob"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Student ID <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    :value="studentProfile.roll_number"
                    readonly
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Degree <span class="text-danger">*</span></label
                  ><select
                    class="form-select"
                    v-model="studentProfile.course"
                    required
                  >
                    <option value="">Select degree</option>
                    <option
                      v-for="degree in degreeOptions"
                      :key="degree"
                      :value="degree"
                    >
                      {{ degree }}
                    </option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Branch <span class="text-danger">*</span></label
                  ><select
                    class="form-select"
                    v-model="studentProfile.branch"
                    required
                  >
                    <option value="">Select branch</option>
                    <option
                      v-for="branch in branchOptions"
                      :key="branch"
                      :value="branch"
                    >
                      {{ branch }}
                    </option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Graduation year <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="number"
                    min="2020"
                    max="2100"
                    v-model="studentProfile.graduation_year"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >CGPA <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="number"
                    min="0"
                    max="10"
                    step="0.01"
                    v-model="studentProfile.cgpa"
                    required
                  />
                </div>
                <div class="col-12">
                  <label class="form-label">Experience</label
                  ><textarea
                    class="form-control"
                    v-model.trim="studentProfile.experience"
                  ></textarea>
                </div>
                <div class="col-12">
                  <label class="form-label"
                    >Address line 1 <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentProfile.address_line1"
                    required
                  />
                </div>
                <div class="col-md-8">
                  <label class="form-label">Address line 2</label
                  ><input
                    class="form-control"
                    v-model.trim="studentProfile.address_line2"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">Landmark</label
                  ><input
                    class="form-control"
                    v-model.trim="studentProfile.landmark"
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Pincode <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    inputmode="numeric"
                    pattern="[0-9]{6}"
                    maxlength="6"
                    v-model="studentProfile.pincode"
                    @input="lookupPincode(studentProfile)"
                    required
                  /><small
                    v-if="pincodeLoading"
                    class="text-primary d-block mt-1"
                    >Finding city and state...</small
                  ><small
                    v-else-if="pincodeMessage.student"
                    class="d-block mt-1"
                    :class="
                      pincodeMessage.student.includes('filled automatically')
                        ? 'text-success'
                        : 'text-muted'
                    "
                    >{{ pincodeMessage.student }}</small
                  >
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >City <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    :value="studentProfile.city"
                    readonly
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >State <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    :value="studentProfile.state"
                    readonly
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Country <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentProfile.country"
                    required
                  />
                </div>
                <div class="col-12">
                  <label class="form-label">Replace resume</label
                  ><input
                    ref="profileResume"
                    class="form-control"
                    type="file"
                    accept=".pdf,.doc,.docx"
                  />
                </div>
                <div class="col-12 d-flex flex-wrap gap-2">
                  <button class="btn" :class="themeButtonClass">Save profile</button>
                  <button class="btn btn-outline-secondary" type="button" @click="cancelProfileChanges">Cancel</button>
                </div>
              </div>
            </div>
          </form>
          <form
            v-else-if="user"
            class="card border-0 shadow-sm"
            @submit.prevent="saveCompanyProfile"
          >
            <div class="card-body p-4">
              <h1 class="h3">Company Profile</h1>
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label">Company name</label
                  ><input
                    class="form-control"
                    v-model.trim="companyProfile.name"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label">Industry</label
                  ><input
                    class="form-control"
                    v-model.trim="companyProfile.industry"
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label">HR name</label
                  ><input
                    class="form-control"
                    v-model.trim="companyProfile.hr_name"
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label">HR email</label
                  ><input
                    class="form-control"
                    type="email"
                    v-model.trim="companyProfile.hr_email"
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label">Website</label
                  ><input
                    class="form-control"
                    type="url"
                    v-model.trim="companyProfile.website"
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label">Headquarters</label
                  ><input
                    class="form-control"
                    v-model.trim="companyProfile.headquarters"
                  />
                </div>
                <div class="col-12">
                  <label class="form-label">Description</label
                  ><textarea
                    class="form-control"
                    v-model.trim="companyProfile.description"
                  ></textarea>
                </div>
                <div class="col-12 d-flex flex-wrap gap-2">
                  <button class="btn" :class="themeButtonClass">Save profile</button>
                  <button class="btn btn-outline-secondary" type="button" @click="cancelProfileChanges">Cancel</button>
                </div>
              </div>
            </div>
          </form>
        </div>
      </section>
`;
