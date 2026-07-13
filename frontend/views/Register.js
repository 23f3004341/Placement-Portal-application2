window.RegisterView = `
      <section
        v-else-if="page === 'register'"
        class="row justify-content-center"
      >
        <div class="col-xl-9">
          <div class="card shadow-sm border-0">
            <div class="card-body p-4">
              <div
                class="d-flex justify-content-between align-items-center mb-3"
              >
                <h1 class="h3 mb-0">Register</h1>
                <div class="btn-group">
                  <button
                    class="btn"
                    :class="
                      registerRole === 'student'
                        ? 'btn-primary'
                        : 'btn-outline-primary'
                    "
                    @click="registerRole = 'student'"
                  >
                    Student</button
                  ><button
                    class="btn"
                    :class="
                      registerRole === 'company'
                        ? 'btn-primary'
                        : 'btn-outline-primary'
                    "
                    @click="registerRole = 'company'"
                  >
                    Company
                  </button>
                </div>
              </div>
              <form
                v-if="registerRole === 'student'"
                class="row g-3"
                @submit.prevent="registerStudent"
              >
                <div class="col-md-4">
                  <label class="form-label"
                    >First name <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentRegister.first_name"
                    placeholder="Enter first name"
                    minlength="2"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">Middle name</label
                  ><input
                    class="form-control"
                    v-model.trim="studentRegister.middle_name"
                    placeholder="Enter middle name"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Last name <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentRegister.last_name"
                    placeholder="Enter last name"
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
                    v-model.trim="studentRegister.email"
                    placeholder="Enter email address"
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Password <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="password"
                    minlength="6"
                    v-model="studentRegister.password"
                    placeholder="Create password"
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Confirm password <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="password"
                    minlength="6"
                    v-model="studentRegister.confirm_password"
                    placeholder="Repeat password"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Contact <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    inputmode="numeric"
                    pattern="[0-9]{10}"
                    maxlength="10"
                    v-model="studentRegister.contact"
                    @input="digitsOnly(studentRegister, 'contact', 10)"
                    placeholder="Enter 10-digit contact number"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">Gender</label
                  ><select class="form-select" v-model="studentRegister.gender">
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
                  <label class="form-label">Date of birth</label
                  ><input
                    class="form-control"
                    type="date"
                    v-model="studentRegister.dob"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >Degree <span class="text-danger">*</span></label
                  ><select
                    class="form-select"
                    v-model="studentRegister.course"
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
                    v-model="studentRegister.branch"
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
                    v-model="studentRegister.graduation_year"
                    placeholder="Enter graduation year"
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
                    v-model="studentRegister.cgpa"
                    placeholder="Enter CGPA"
                    required
                  />
                </div>
                <div class="col-12">
                  <label class="form-label">Experience</label
                  ><textarea
                    class="form-control"
                    v-model.trim="studentRegister.experience"
                    placeholder="Briefly describe internships, projects, or experience"
                  ></textarea>
                </div>
                <div class="col-12">
                  <label class="form-label"
                    >Address line 1 <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentRegister.address_line1"
                    placeholder="House number, street, area"
                    required
                  />
                </div>
                <div class="col-md-8">
                  <label class="form-label">Address line 2</label
                  ><input
                    class="form-control"
                    v-model.trim="studentRegister.address_line2"
                    placeholder="Apartment, locality"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">Landmark</label
                  ><input
                    class="form-control"
                    v-model.trim="studentRegister.landmark"
                    placeholder="Nearby landmark"
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
                    v-model="studentRegister.pincode"
                    @input="lookupPincode(studentRegister)"
                    placeholder="Enter 6-digit pincode"
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
                    :value="studentRegister.city"
                    placeholder="Filled automatically from pincode"
                    readonly
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >State <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    :value="studentRegister.state"
                    placeholder="Filled automatically from pincode"
                    readonly
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Country <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="studentRegister.country"
                    placeholder="Enter country"
                    required
                  />
                </div>
                <div class="col-12">
                  <label class="form-label"
                    >Resume (PDF/DOC/DOCX)
                    <span class="text-danger">*</span></label
                  ><input
                    ref="studentResume"
                    class="form-control"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    required
                  />
                </div>
                <div class="col-12">
                  <button class="btn btn-primary">Register student</button>
                </div>
              </form>
              <form v-else class="row g-3" @submit.prevent="registerCompany">
                <div class="col-md-6">
                  <label class="form-label"
                    >Company name <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.company_name"
                    placeholder="Enter company name"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label"
                    >Industry <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.industry"
                    placeholder="Enter industry"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label"
                    >Company email <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="email"
                    v-model.trim="companyRegister.email"
                    placeholder="Enter company email"
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Password <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="password"
                    minlength="6"
                    v-model="companyRegister.password"
                    placeholder="Create password"
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Confirm password <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="password"
                    minlength="6"
                    v-model="companyRegister.confirm_password"
                    placeholder="Repeat password"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >HR first name <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.hr_first_name"
                    placeholder="Enter HR first name"
                    required
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">HR middle name</label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.hr_middle_name"
                    placeholder="Enter HR middle name"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label"
                    >HR last name <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.hr_last_name"
                    placeholder="Enter HR last name"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label"
                    >HR email <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="email"
                    v-model.trim="companyRegister.hr_email"
                    placeholder="Enter HR email"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label">HR phone</label
                  ><input
                    class="form-control"
                    inputmode="numeric"
                    pattern="[0-9]{10}"
                    maxlength="10"
                    v-model="companyRegister.hr_phone"
                    @input="digitsOnly(companyRegister, 'hr_phone', 10)"
                    placeholder="Enter HR phone number"
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label"
                    >Website <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    type="url"
                    v-model.trim="companyRegister.website"
                    placeholder="https://example.com"
                    required
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label"
                    >Headquarters <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.headquarters"
                    placeholder="Enter headquarters location"
                    required
                  />
                </div>
                <div class="col-12">
                  <label class="form-label"
                    >Address line 1 <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.address_line1"
                    placeholder="Office address line 1"
                    required
                  />
                </div>
                <div class="col-md-8">
                  <label class="form-label">Address line 2</label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.address_line2"
                    placeholder="Office address line 2"
                  />
                </div>
                <div class="col-md-4">
                  <label class="form-label">Landmark</label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.landmark"
                    placeholder="Nearby landmark"
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
                    v-model="companyRegister.pincode"
                    @input="lookupPincode(companyRegister)"
                    placeholder="Enter 6-digit pincode"
                    required
                  /><small
                    v-if="pincodeLoading"
                    class="text-primary d-block mt-1"
                    >Finding city and state...</small
                  ><small
                    v-else-if="pincodeMessage.company"
                    class="d-block mt-1"
                    :class="
                      pincodeMessage.company.includes('filled automatically')
                        ? 'text-success'
                        : 'text-muted'
                    "
                    >{{ pincodeMessage.company }}</small
                  >
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >City <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    :value="companyRegister.city"
                    placeholder="Filled automatically from pincode"
                    readonly
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >State <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    :value="companyRegister.state"
                    placeholder="Filled automatically from pincode"
                    readonly
                    required
                  />
                </div>
                <div class="col-md-3">
                  <label class="form-label"
                    >Country <span class="text-danger">*</span></label
                  ><input
                    class="form-control"
                    v-model.trim="companyRegister.country"
                    placeholder="Enter country"
                    required
                  />
                </div>
                <div class="col-12">
                  <label class="form-label">Description</label
                  ><textarea
                    class="form-control"
                    v-model.trim="companyRegister.description"
                    placeholder="Tell students about your company"
                  ></textarea>
                </div>
                <div class="col-12">
                  <button class="btn btn-primary">Register company</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </section>
`;
