<template>
<div v-cloak>
    <nav class="navbar navbar-expand-lg sticky-top spa-navbar">
        <div class="container-fluid px-lg-4">
            <a class="navbar-brand fw-bold clickable" @click="go('home')">Placement Portal</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav"><span class="navbar-toggler-icon"></span></button>
            <div id="mainNav" class="collapse navbar-collapse">
                <div class="navbar-nav ms-auto align-items-lg-center gap-lg-1">
                    <template v-if="user">
                        <button class="btn btn-link nav-link" :class="{active:page==='dashboard'}" @click="go('dashboard')">Dashboard</button>
                        <button v-if="user.role==='admin'" class="btn btn-link nav-link" @click="go('admin-companies')">Companies</button>
                        <button v-if="user.role==='admin'" class="btn btn-link nav-link" @click="go('admin-students')">Students</button>
                        <button v-if="user.role==='admin'" class="btn btn-link nav-link" @click="go('admin-drives')">Drives</button>
                        <button v-if="user.role==='admin'" class="btn btn-link nav-link" @click="go('admin-applications')">Applications</button>
                        <button v-if="user.role==='company'" class="btn btn-link nav-link" :class="{active:page==='company-drives'}" @click="go('company-drives')">Drives</button>
                        <button v-if="user.role==='company'" class="btn btn-link nav-link" :class="{active:page==='company-applications'}" @click="go('company-applications')">Applicants</button>
                        <button v-if="user.role==='student'" class="btn btn-link nav-link" :class="{active:page==='student-drives'}" @click="go('student-drives')">Find Jobs</button>
                        <button v-if="user.role==='student'" class="btn btn-link nav-link" :class="{active:page==='student-applications'}" @click="go('student-applications')">My Applications</button>
                        <button v-if="user.role!=='admin'" class="btn btn-link nav-link" :class="{active:page==='profile'}" @click="go('profile')">Profile</button>
                        <button v-if="user.role!=='admin'" class="btn btn-link nav-link" :class="{active:page==='ats'}" @click="go('ats')">ATS</button>
                        <div class="notification-menu">
                            <button class="btn btn-outline-primary btn-sm notification-toggle" type="button" @click="toggleNotifications">
                                Notifications
                                <span v-if="unreadCount" class="notification-count">{{ unreadCount }}</span>
                            </button>
                            <div v-if="showNotifications" class="notification-panel shadow-sm">
                                <div class="notification-panel-header">
                                    <strong>Notifications</strong>
                                    <button v-if="unreadCount" class="btn btn-link btn-sm p-0" @click="markAllNotificationsRead">Mark all read</button>
                                </div>
                                <div v-if="notifications.length" class="notification-list">
                                    <button
                                        v-for="item in notifications"
                                        :key="item.id"
                                        class="notification-item"
                                        :class="{unread: !item.is_read}"
                                        type="button"
                                        @click="openNotification(item)"
                                    >
                                        <span class="notification-title">{{ item.title }}</span>
                                        <span class="notification-message">{{ item.message }}</span>
                                        <span class="notification-time">{{ formatDate(item.created_at) }}</span>
                                    </button>
                                </div>
                                <div v-else class="notification-empty">No notifications yet.</div>
                            </div>
                        </div>
                        <button class="btn btn-outline-danger btn-sm ms-lg-2" @click="logout">Logout</button>
                    </template>
                    <template v-else>
                        <button class="btn btn-link nav-link" @click="go('analytics')">Placement Analytics</button>
                        <button class="btn btn-outline-primary btn-sm" @click="go('login')">Login</button>
                        <button class="btn btn-primary btn-sm" @click="go('register')">Register</button>
                    </template>
                </div>
            </div>
        </div>
    </nav>

    <main class="container-fluid px-3 px-lg-4 py-4 spa-main">
        <div v-if="alert.message" class="alert alert-dismissible" :class="'alert-'+alert.type" role="alert">
            {{ alert.message }}<button class="btn-close" @click="alert.message=''" aria-label="Close"></button>
        </div>
        <div v-if="loading" class="position-fixed top-0 start-0 w-100 h-100 d-grid bg-white bg-opacity-75" style="z-index:2000;place-items:center"><div class="spinner-border text-primary" aria-label="Loading"></div></div>

        <section v-if="page==='home'">
            <div class="card border-0 mb-4 landing-hero"><div class="card-body p-4 p-lg-5 text-center"><span class="eyebrow">Campus recruitment, simplified</span><h1 class="display-5 fw-bold mt-3">Northbridge Placement Portal</h1><p class="lead mb-0">One place for opportunities, applications, interviews, and placements.</p><div class="d-flex flex-wrap justify-content-center gap-2 mt-4"><button class="btn btn-light px-4" @click="go('login')">Login</button><button class="btn btn-outline-light px-4" @click="go('register')">Create account</button><button class="btn btn-outline-light px-4" @click="go('analytics')">Placement analytics</button></div></div></div>
            <div class="row g-3 mb-4">
                <div v-for="(value,key) in publicStats.totals" :key="key" class="col-6 col-lg-3"><div class="card h-100 border-0 metric-card"><div class="card-body"><div class="metric-label text-capitalize">{{ key }}</div><div class="metric-value">{{ value }}</div></div></div></div>
            </div>
            <div class="row g-3"><div class="col-md-4"><div class="card h-100 border-0 feature-card"><div class="card-body"><div class="feature-icon">01</div><h2 class="h5">For students</h2><p class="text-secondary mb-0">Discover eligible roles, apply, track interviews, and download placement confirmations.</p></div></div></div><div class="col-md-4"><div class="card h-100 border-0 feature-card"><div class="card-body"><div class="feature-icon">02</div><h2 class="h5">For companies</h2><p class="text-secondary mb-0">Publish approved drives, review candidates, schedule interviews, and share decisions.</p></div></div></div><div class="col-md-4"><div class="card h-100 border-0 feature-card"><div class="card-body"><div class="feature-icon">03</div><h2 class="h5">For the placement cell</h2><p class="text-secondary mb-0">Manage registrations and drives while monitoring institution-wide outcomes.</p></div></div></div></div>
        </section>

        <section v-else-if="page==='analytics'">
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4"><div><h1 class="h3 mb-1">Public Placement Analytics</h1><p class="text-secondary mb-0">Aggregated statistics only—no student-level information.</p></div><button class="btn btn-outline-secondary" @click="go('home')">Back to home</button></div>
            <div class="row g-3">
                <div class="col-12 col-lg-6"><div class="card shadow-sm border-0"><div class="card-body"><h2 class="h5">Monthly placement trend</h2><div class="chart-box"><canvas id="trendChart"></canvas></div></div></div></div>
                <div class="col-12 col-lg-6"><div class="card shadow-sm border-0"><div class="card-body"><h2 class="h5">Application funnel</h2><div class="chart-box"><canvas id="funnelChart"></canvas></div></div></div></div>
                <div class="col-12"><div class="card shadow-sm border-0"><div class="card-body"><h2 class="h5">Job demand by skills</h2><div class="chart-box"><canvas id="skillsChart"></canvas></div></div></div></div>
            </div>
        </section>

        <section v-else-if="page==='login'" class="row justify-content-center"><div class="col-md-7 col-lg-5"><form class="card shadow-sm border-0" @submit.prevent="login"><div class="card-body p-4"><h1 class="h3 mb-3">Login</h1><label class="form-label">Role</label><select class="form-select mb-3" v-model="loginForm.role" required><option value="student">Student</option><option value="company">Company</option><option value="admin">Admin</option></select><label class="form-label">Email</label><input class="form-control mb-3" type="email" v-model.trim="loginForm.email" required><label class="form-label">Password</label><input class="form-control mb-3" type="password" minlength="6" v-model="loginForm.password" required><button class="btn btn-primary w-100">Login</button></div></form></div></section>

        <section v-else-if="page==='register'" class="row justify-content-center"><div class="col-xl-9"><div class="card shadow-sm border-0"><div class="card-body p-4"><div class="d-flex justify-content-between align-items-center mb-3"><h1 class="h3 mb-0">Register</h1><div class="btn-group"><button class="btn" :class="registerRole==='student'?'btn-primary':'btn-outline-primary'" @click="registerRole='student'">Student</button><button class="btn" :class="registerRole==='company'?'btn-primary':'btn-outline-primary'" @click="registerRole='company'">Company</button></div></div>
            <form v-if="registerRole==='student'" class="row g-3" @submit.prevent="registerStudent"><div class="col-md-4"><label class="form-label">First name <span class="text-danger">*</span></label><input class="form-control" v-model.trim="studentRegister.first_name" placeholder="Enter first name" minlength="2" required></div><div class="col-md-4"><label class="form-label">Middle name</label><input class="form-control" v-model.trim="studentRegister.middle_name" placeholder="Enter middle name"></div><div class="col-md-4"><label class="form-label">Last name <span class="text-danger">*</span></label><input class="form-control" v-model.trim="studentRegister.last_name" placeholder="Enter last name" minlength="1" required></div><div class="col-md-6"><label class="form-label">Email <span class="text-danger">*</span></label><input class="form-control" type="email" v-model.trim="studentRegister.email" placeholder="Enter email address" required></div><div class="col-md-3"><label class="form-label">Password <span class="text-danger">*</span></label><input class="form-control" type="password" minlength="6" v-model="studentRegister.password" placeholder="Create password" required></div><div class="col-md-3"><label class="form-label">Confirm password <span class="text-danger">*</span></label><input class="form-control" type="password" minlength="6" v-model="studentRegister.confirm_password" placeholder="Repeat password" required></div><div class="col-md-4"><label class="form-label">Contact <span class="text-danger">*</span></label><input class="form-control" inputmode="numeric" pattern="[0-9]{10}" maxlength="10" v-model="studentRegister.contact" @input="digitsOnly(studentRegister, 'contact', 10)" placeholder="Enter 10-digit contact number" required></div><div class="col-md-4"><label class="form-label">Gender</label><select class="form-select" v-model="studentRegister.gender"><option value="">Select gender</option><option v-for="gender in genderOptions" :key="gender" :value="gender">{{ gender }}</option></select></div><div class="col-md-4"><label class="form-label">Date of birth</label><input class="form-control" type="date" v-model="studentRegister.dob"></div><div class="col-md-4"><label class="form-label">Degree <span class="text-danger">*</span></label><select class="form-select" v-model="studentRegister.course" required><option value="">Select degree</option><option v-for="degree in degreeOptions" :key="degree" :value="degree">{{ degree }}</option></select></div><div class="col-md-4"><label class="form-label">Branch <span class="text-danger">*</span></label><select class="form-select" v-model="studentRegister.branch" required><option value="">Select branch</option><option v-for="branch in branchOptions" :key="branch" :value="branch">{{ branch }}</option></select></div><div class="col-md-4"><label class="form-label">Graduation year <span class="text-danger">*</span></label><input class="form-control" type="number" min="2020" max="2100" v-model="studentRegister.graduation_year" placeholder="Enter graduation year" required></div><div class="col-md-4"><label class="form-label">CGPA <span class="text-danger">*</span></label><input class="form-control" type="number" min="0" max="10" step="0.01" v-model="studentRegister.cgpa" placeholder="Enter CGPA" required></div><div class="col-md-8"><label class="form-label">Skills <span class="text-danger">*</span></label><input class="form-control" v-model.trim="studentRegister.skills" placeholder="Python, SQL, Vue" required></div><div class="col-12"><label class="form-label">Experience</label><textarea class="form-control" v-model.trim="studentRegister.experience" placeholder="Briefly describe internships, projects, or experience"></textarea></div><div class="col-12"><label class="form-label">Address line 1 <span class="text-danger">*</span></label><input class="form-control" v-model.trim="studentRegister.address_line1" placeholder="House number, street, area" required></div><div class="col-md-8"><label class="form-label">Address line 2</label><input class="form-control" v-model.trim="studentRegister.address_line2" placeholder="Apartment, locality"></div><div class="col-md-4"><label class="form-label">Landmark</label><input class="form-control" v-model.trim="studentRegister.landmark" placeholder="Nearby landmark"></div><div class="col-md-3"><label class="form-label">Pincode <span class="text-danger">*</span></label><input class="form-control" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" v-model="studentRegister.pincode" @input="lookupPincode(studentRegister)" placeholder="Enter 6-digit pincode" required><small v-if="pincodeLoading" class="text-primary d-block mt-1">Finding city and state...</small><small v-else-if="pincodeMessage.student" class="d-block mt-1" :class="pincodeMessage.student.includes('filled automatically') ? 'text-success' : 'text-muted'">{{ pincodeMessage.student }}</small></div><div class="col-md-3"><label class="form-label">City <span class="text-danger">*</span></label><input class="form-control" :value="studentRegister.city" placeholder="Filled automatically from pincode" readonly required></div><div class="col-md-3"><label class="form-label">State <span class="text-danger">*</span></label><input class="form-control" :value="studentRegister.state" placeholder="Filled automatically from pincode" readonly required></div><div class="col-md-3"><label class="form-label">Country <span class="text-danger">*</span></label><input class="form-control" v-model.trim="studentRegister.country" placeholder="Enter country" required></div><div class="col-12"><label class="form-label">Resume (PDF/DOC/DOCX) <span class="text-danger">*</span></label><input ref="studentResume" class="form-control" type="file" accept=".pdf,.doc,.docx" required></div><div class="col-12"><button class="btn btn-primary">Register student</button></div></form>
            <form v-else class="row g-3" @submit.prevent="registerCompany"><div class="col-md-6"><label class="form-label">Company name <span class="text-danger">*</span></label><input class="form-control" v-model.trim="companyRegister.company_name" placeholder="Enter company name" required></div><div class="col-md-6"><label class="form-label">Industry <span class="text-danger">*</span></label><input class="form-control" v-model.trim="companyRegister.industry" placeholder="Enter industry" required></div><div class="col-md-6"><label class="form-label">Company email <span class="text-danger">*</span></label><input class="form-control" type="email" v-model.trim="companyRegister.email" placeholder="Enter company email" required></div><div class="col-md-3"><label class="form-label">Password <span class="text-danger">*</span></label><input class="form-control" type="password" minlength="6" v-model="companyRegister.password" placeholder="Create password" required></div><div class="col-md-3"><label class="form-label">Confirm password <span class="text-danger">*</span></label><input class="form-control" type="password" minlength="6" v-model="companyRegister.confirm_password" placeholder="Repeat password" required></div><div class="col-md-4"><label class="form-label">HR first name <span class="text-danger">*</span></label><input class="form-control" v-model.trim="companyRegister.hr_first_name" placeholder="Enter HR first name" required></div><div class="col-md-4"><label class="form-label">HR middle name</label><input class="form-control" v-model.trim="companyRegister.hr_middle_name" placeholder="Enter HR middle name"></div><div class="col-md-4"><label class="form-label">HR last name <span class="text-danger">*</span></label><input class="form-control" v-model.trim="companyRegister.hr_last_name" placeholder="Enter HR last name" required></div><div class="col-md-6"><label class="form-label">HR email <span class="text-danger">*</span></label><input class="form-control" type="email" v-model.trim="companyRegister.hr_email" placeholder="Enter HR email" required></div><div class="col-md-6"><label class="form-label">HR phone</label><input class="form-control" inputmode="numeric" pattern="[0-9]{10}" maxlength="10" v-model="companyRegister.hr_phone" @input="digitsOnly(companyRegister, 'hr_phone', 10)" placeholder="Enter HR phone number"></div><div class="col-md-6"><label class="form-label">Website <span class="text-danger">*</span></label><input class="form-control" type="url" v-model.trim="companyRegister.website" placeholder="https://example.com" required></div><div class="col-md-6"><label class="form-label">Headquarters <span class="text-danger">*</span></label><input class="form-control" v-model.trim="companyRegister.headquarters" placeholder="Enter headquarters location" required></div><div class="col-12"><label class="form-label">Address line 1 <span class="text-danger">*</span></label><input class="form-control" v-model.trim="companyRegister.address_line1" placeholder="Office address line 1" required></div><div class="col-md-8"><label class="form-label">Address line 2</label><input class="form-control" v-model.trim="companyRegister.address_line2" placeholder="Office address line 2"></div><div class="col-md-4"><label class="form-label">Landmark</label><input class="form-control" v-model.trim="companyRegister.landmark" placeholder="Nearby landmark"></div><div class="col-md-3"><label class="form-label">Pincode <span class="text-danger">*</span></label><input class="form-control" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" v-model="companyRegister.pincode" @input="lookupPincode(companyRegister)" placeholder="Enter 6-digit pincode" required><small v-if="pincodeLoading" class="text-primary d-block mt-1">Finding city and state...</small><small v-else-if="pincodeMessage.company" class="d-block mt-1" :class="pincodeMessage.company.includes('filled automatically') ? 'text-success' : 'text-muted'">{{ pincodeMessage.company }}</small></div><div class="col-md-3"><label class="form-label">City <span class="text-danger">*</span></label><input class="form-control" :value="companyRegister.city" placeholder="Filled automatically from pincode" readonly required></div><div class="col-md-3"><label class="form-label">State <span class="text-danger">*</span></label><input class="form-control" :value="companyRegister.state" placeholder="Filled automatically from pincode" readonly required></div><div class="col-md-3"><label class="form-label">Country <span class="text-danger">*</span></label><input class="form-control" v-model.trim="companyRegister.country" placeholder="Enter country" required></div><div class="col-12"><label class="form-label">Description</label><textarea class="form-control" v-model.trim="companyRegister.description" placeholder="Tell students about your company"></textarea></div><div class="col-12"><button class="btn btn-primary">Register company</button></div></form>
        </div></div></div></section>

        <section v-else-if="page==='dashboard'">
            <h1 class="h3 mb-3">{{ roleTitle }} Dashboard</h1>
            <div class="row g-3 mb-4"><div v-for="(value,key) in dashboard.metrics" :key="key" class="col-6 col-lg-3"><div class="card border-0 metric-card"><div class="card-body"><div class="metric-label text-capitalize">{{ key.replaceAll('_',' ') }}</div><div class="metric-value">{{ value }}</div></div></div></div></div>
            <div v-if="user.role==='student'" class="card border-0 shadow-sm"><div class="card-body"><h2 class="h5">Welcome, {{ dashboard.student?.user.name }}</h2><p class="text-secondary">Use Find Jobs to search by company, position, or required skill.</p><export-panel :value="dashboard.latest_export" @start="startExport"></export-panel><div class="d-flex flex-wrap align-items-center gap-2 mt-3"><span class="small text-secondary">Placement activity report</span><a class="btn btn-outline-secondary btn-sm" href="/api/student/report?format=html" download>Download HTML</a><a class="btn btn-outline-secondary btn-sm" href="/api/student/report?format=pdf" download>Download PDF</a></div></div></div>
            <div v-if="user.role==='company'" class="card border-0 shadow-sm"><div class="card-body"><h2 class="h5">{{ dashboard.company?.name }}</h2><p class="text-secondary">Manage jobs, applicants, interviews, feedback, offers, and placements.</p><export-panel :value="dashboard.latest_export" @start="startExport"></export-panel></div></div>
            <div v-if="user.role==='admin'" class="card border-0 shadow-sm"><div class="card-body"><h2 class="h5">Recent applications</h2><div class="table-responsive"><table class="table"><thead><tr><th>Student</th><th>Company</th><th>Position</th><th>Status</th></tr></thead><tbody><tr v-for="item in dashboard.recent_applications"><td>{{ item.student.user.name }}</td><td>{{ item.drive.company }}</td><td>{{ item.drive.title }}</td><td><status-badge :value="item.status"></status-badge></td></tr></tbody></table></div></div></div>
        </section>

        <section v-else-if="page==='admin-companies'"><list-header title="Companies" placeholder="Search name or industry" v-model="search" @search="loadAdminCompanies"></list-header><div class="table-responsive card shadow-sm border-0"><table class="table mb-0"><thead><tr><th>Company</th><th>Industry</th><th>Approval</th><th>Account</th><th>Actions</th></tr></thead><tbody><tr v-for="c in companies"><td>{{ c.name }}<br><small>{{ c.user.email }}</small></td><td>{{ c.industry || '-' }}</td><td>{{ c.user.approved?'Approved':'Pending' }}</td><td>{{ c.user.active?'Active':'Inactive' }}</td><td class="d-flex flex-wrap gap-1"><button class="btn btn-success btn-sm" @click="adminStatus('companies',c.id,'approve')">Approve</button><button class="btn btn-warning btn-sm" @click="adminStatus('companies',c.id,c.user.active?'blacklist':'activate')">{{ c.user.active?'Blacklist':'Activate' }}</button><button class="btn btn-danger btn-sm" @click="adminDelete('companies',c.id)">Remove</button></td></tr></tbody></table></div></section>
        <section v-else-if="page==='admin-students'"><list-header title="Students" placeholder="Search name, ID, or contact" v-model="search" @search="loadAdminStudents"></list-header><div class="table-responsive card shadow-sm border-0"><table class="table mb-0"><thead><tr><th>Student</th><th>Roll</th><th>Course</th><th>Contact</th><th>Actions</th></tr></thead><tbody><tr v-for="s in students"><td>{{ s.user.name }}</td><td>{{ s.roll_number }}</td><td>{{ s.course }} / {{ s.branch }}</td><td>{{ s.user.contact }}</td><td class="d-flex gap-1"><button class="btn btn-warning btn-sm" @click="adminStatus('students',s.id,s.user.active?'blacklist':'activate')">{{ s.user.active?'Blacklist':'Activate' }}</button><button class="btn btn-danger btn-sm" @click="adminDelete('students',s.id)">Remove</button></td></tr></tbody></table></div></section>
        <section v-else-if="page==='admin-drives'"><list-header title="Placement Drives" placeholder="Search company, position, or skill" v-model="search" @search="loadAdminDrives"></list-header><drive-table :drives="drives" admin @action="adminDriveAction"></drive-table></section>
        <section v-else-if="page==='admin-applications'"><h1 class="h3 mb-3">All Applications</h1><application-table :applications="applications"></application-table></section>

        <section v-else-if="page==='company-drives'"><div class="d-flex flex-wrap justify-content-between align-items-center mb-3"><h1 class="h3 mb-0">Job Positions</h1><button class="btn btn-primary" @click="showDriveForm=!showDriveForm">{{ showDriveForm?'Close form':'Post new job' }}</button></div><form v-if="showDriveForm" class="card border-0 shadow-sm mb-4" @submit.prevent="saveDrive"><div class="card-body"><div class="row g-3"><div class="col-md-6"><label class="form-label">Title <span class="text-danger">*</span></label><input class="form-control" v-model.trim="driveForm.title" required></div><div class="col-md-3"><label class="form-label">Type</label><select class="form-select" v-model="driveForm.job_type"><option value="full-time">Full-time</option><option value="internship">Internship</option><option value="contract">Contract</option></select></div><div class="col-md-3"><label class="form-label">Deadline <span class="text-danger">*</span></label><input class="form-control" type="date" :min="today" v-model="driveForm.deadline" required></div><div class="col-md-4"><label class="form-label">Location</label><input class="form-control" v-model.trim="driveForm.location"></div><div class="col-md-2"><label class="form-label">Salary</label><input class="form-control" type="number" min="0" step="0.01" v-model="driveForm.salary"></div><div class="col-md-2"><label class="form-label">Openings</label><input class="form-control" type="number" min="1" v-model="driveForm.openings"></div><div class="col-md-2"><label class="form-label">Minimum CGPA</label><input class="form-control" type="number" min="0" max="10" step="0.01" v-model="driveForm.min_cgpa"></div><div class="col-md-2"><label class="form-label">Unit</label><select class="form-select" v-model="driveForm.salary_unit"><option value="lpa">LPA</option><option value="k_month">K/month</option></select></div><div class="col-md-4"><label class="form-label">Eligible degrees</label><select class="form-select" multiple size="7" v-model="driveForm.eligible_degrees_list"><option v-for="degree in degreeOptions" :key="degree" :value="degree">{{ degree }}</option></select><small class="text-secondary">Hold Cmd/Ctrl to select more than one.</small></div><div class="col-md-4"><label class="form-label">Eligible branches</label><select class="form-select" multiple size="7" v-model="driveForm.eligible_branches_list"><option v-for="branch in branchOptions" :key="branch" :value="branch">{{ branch }}</option></select><small class="text-secondary">Leave empty if all branches are eligible.</small></div><div class="col-md-4"><label class="form-label">Eligible graduation years</label><input class="form-control" v-model.trim="driveForm.eligible_years" placeholder="2026, 2027"><small class="text-secondary">Comma-separated years.</small></div><div class="col-md-6"><label class="form-label">Required skills</label><input class="form-control" v-model.trim="driveForm.skills_required" required placeholder="Python, SQL, Vue"></div><div class="col-md-6"><label class="form-label">Experience required</label><input class="form-control" v-model.trim="driveForm.experience_required" placeholder="0-2 years"></div><div class="col-md-6"><label class="form-label">Benefits</label><textarea class="form-control" v-model.trim="driveForm.benefits"></textarea></div><div class="col-md-6"><label class="form-label">Job description <span class="text-danger">*</span></label><textarea class="form-control" v-model.trim="driveForm.description" required></textarea></div><div class="col-12"><button class="btn btn-primary">{{ driveForm.id?'Update and resubmit':'Submit for approval' }}</button></div></div></div></form><drive-table :drives="drives" company @edit="editDrive" @action="companyDriveAction"></drive-table></section>

        <section v-else-if="page==='company-applications'"><h1 class="h3 mb-3">Applicants</h1><div class="row g-3"><div v-for="a in applications" :key="a.id" class="col-12"><div class="card border-0 shadow-sm"><div class="card-body"><div class="row g-3"><div class="col-lg-3"><h2 class="h5">{{ a.student.user.name }}</h2><div>{{ a.student.roll_number }}</div><div>{{ a.student.course }} · {{ a.student.cgpa ?? '-' }} CGPA</div><div class="small text-secondary">Skills: {{ a.student.skills || '-' }}</div><a v-if="a.student.resume_url" :href="a.student.resume_url" target="_blank">View résumé</a></div><div class="col-lg-3"><strong>{{ a.drive.title }}</strong><br><status-badge :value="a.status"></status-badge><p class="small mt-2 mb-0">Feedback: {{ a.feedback || '-' }}</p></div><div class="col-lg-3"><label class="form-label">Status and feedback</label><select class="form-select form-select-sm mb-2" v-model="a.nextStatus"><option value="shortlisted">Shortlisted</option><option value="offer">Offer</option><option value="rejected">Rejected</option><option value="placed">Placed</option></select><textarea class="form-control form-control-sm mb-2" v-model="a.nextFeedback" placeholder="Feedback to student"></textarea><button class="btn btn-primary btn-sm" @click="updateApplication(a)">Update</button></div><div class="col-lg-3"><label class="form-label">Schedule interview</label><input class="form-control form-control-sm mb-2" type="datetime-local" v-model="a.interviewAt"><input class="form-control form-control-sm mb-2" v-model="a.interviewLocation" placeholder="Link or location"><button class="btn btn-outline-info btn-sm" @click="scheduleInterview(a)">Schedule</button><div v-for="i in a.interviews" class="small mt-2 border-top pt-2">{{ formatDate(i.scheduled_at) }} · {{ i.mode }}<input class="form-control form-control-sm my-1" v-model="i.nextFeedback" placeholder="Interview feedback"><select class="form-select form-select-sm mb-1" v-model="i.nextResult"><option value="">Pending</option><option value="offer">Offer</option><option value="rejected">Rejected</option></select><button class="btn btn-outline-primary btn-sm" @click="completeInterview(i)">Save feedback</button></div></div></div></div></div></div></div></section>

        <section v-else-if="page==='student-drives'"><list-header title="Approved Job Positions" placeholder="Search company, position, or required skill" v-model="search" @search="loadStudentDrives"></list-header><div class="form-check form-switch mb-3"><input id="eligibleOnly" class="form-check-input" type="checkbox" v-model="eligibleOnly" @change="loadStudentDrives"><label class="form-check-label" for="eligibleOnly">Show only jobs I am eligible for</label></div><div class="row g-3"><div v-for="d in drives" :key="d.id" class="col-12 col-xl-6"><div class="card border-0 shadow-sm h-100"><div class="card-body"><div class="d-flex justify-content-between"><div><h2 class="h5 mb-1">{{ d.title }}</h2><div class="text-secondary">{{ d.company }} · {{ d.location || 'Location TBA' }}</div></div><span class="badge" :class="d.eligible?'text-bg-success':'text-bg-warning'">{{ d.eligible?'Eligible':'Not eligible' }}</span></div><p class="mt-3 mb-2">{{ d.description }}</p><div><strong>Skills:</strong> {{ d.skills_required || '-' }}</div><div><strong>Experience:</strong> {{ d.experience_required || '-' }}</div><div><strong>Benefits:</strong> {{ d.benefits || '-' }}</div><div><strong>Deadline:</strong> {{ d.deadline }}</div><div v-if="!d.eligible" class="text-danger small">Missing: {{ d.eligibility_reasons.join(', ') }}</div><button class="btn btn-primary mt-3" :disabled="!d.eligible || !!d.application_status" @click="applyDrive(d)">{{ d.application_status ? 'Status: '+d.application_status : 'Apply' }}</button></div></div></div></div></section>

        <section v-else-if="page==='student-applications'"><div class="d-flex justify-content-between align-items-center mb-3"><h1 class="h3 mb-0">Applications & Placement History</h1><button class="btn btn-outline-primary" @click="startExport">Export CSV</button></div><div class="row g-3"><div v-for="a in applications" :key="a.id" class="col-12"><div class="card border-0 shadow-sm"><div class="card-body"><div class="row g-3"><div class="col-lg-4"><h2 class="h5">{{ a.drive.title }}</h2><div>{{ a.drive.company }}</div><div>Applied {{ formatDate(a.applied_at) }}</div></div><div class="col-lg-3"><status-badge :value="a.status"></status-badge><p class="mt-2 mb-0"><strong>Feedback:</strong> {{ a.feedback || '-' }}</p><button v-if="a.status==='applied'" class="btn btn-outline-danger btn-sm mt-2" @click="withdrawApplication(a)">Withdraw</button></div><div class="col-lg-3"><h3 class="h6">Interviews</h3><div v-for="i in a.interviews" class="small mb-2">{{ formatDate(i.scheduled_at) }}<br>{{ i.mode }} · {{ i.location_or_link }}<br><strong>Feedback:</strong> {{ i.feedback || '-' }}</div><span v-if="!a.interviews.length" class="text-secondary">None scheduled</span></div><div class="col-lg-2"><h3 class="h6">Offer / Placement</h3><template v-if="a.placement"><div>{{ a.placement.status }}</div><div>{{ a.placement.package ?? '-' }}</div><a class="btn btn-success btn-sm mt-2" :href="a.placement.offer_letter_url">Download letter</a></template><span v-else class="text-secondary">Not available</span></div></div></div></div></div></div></section>

        <section v-else-if="page==='profile'" class="row justify-content-center"><div class="col-xl-9"><form v-if="user.role==='student'" class="card border-0 shadow-sm" @submit.prevent="saveStudentProfile"><div class="card-body p-4"><h1 class="h3">Student Profile</h1><div class="row g-3"><div class="col-md-6"><label class="form-label">Name</label><input class="form-control" v-model.trim="studentProfile.user.name" required></div><div class="col-md-6"><label class="form-label">Contact</label><input class="form-control" pattern="[0-9]{10}" v-model.trim="studentProfile.user.contact"></div><div class="col-md-4"><label class="form-label">Degree</label><input class="form-control" v-model.trim="studentProfile.course" required></div><div class="col-md-4"><label class="form-label">Branch</label><input class="form-control" v-model.trim="studentProfile.branch" required></div><div class="col-md-4"><label class="form-label">Graduation year</label><input class="form-control" type="number" v-model="studentProfile.graduation_year" required></div><div class="col-md-4"><label class="form-label">CGPA</label><input class="form-control" type="number" min="0" max="10" step=".01" v-model="studentProfile.cgpa"></div><div class="col-md-8"><label class="form-label">Skills</label><input class="form-control" v-model.trim="studentProfile.skills"></div><div class="col-12"><label class="form-label">Experience</label><textarea class="form-control" v-model.trim="studentProfile.experience"></textarea></div><div class="col-12"><label class="form-label">Address</label><textarea class="form-control" v-model.trim="studentProfile.user.address"></textarea></div><div class="col-12"><label class="form-label">Replace résumé</label><input ref="profileResume" class="form-control" type="file" accept=".pdf,.doc,.docx"></div><div class="col-12"><button class="btn btn-primary">Save profile</button></div></div></div></form><form v-else class="card border-0 shadow-sm" @submit.prevent="saveCompanyProfile"><div class="card-body p-4"><h1 class="h3">Company Profile</h1><div class="row g-3"><div class="col-md-6"><label class="form-label">Company name</label><input class="form-control" v-model.trim="companyProfile.name" required></div><div class="col-md-6"><label class="form-label">Industry</label><input class="form-control" v-model.trim="companyProfile.industry"></div><div class="col-md-6"><label class="form-label">HR name</label><input class="form-control" v-model.trim="companyProfile.hr_name"></div><div class="col-md-6"><label class="form-label">HR email</label><input class="form-control" type="email" v-model.trim="companyProfile.hr_email"></div><div class="col-md-6"><label class="form-label">Website</label><input class="form-control" type="url" v-model.trim="companyProfile.website"></div><div class="col-md-6"><label class="form-label">Headquarters</label><input class="form-control" v-model.trim="companyProfile.headquarters"></div><div class="col-12"><label class="form-label">Description</label><textarea class="form-control" v-model.trim="companyProfile.description"></textarea></div><div class="col-12"><button class="btn btn-primary">Save profile</button></div></div></div></form></div></section>

        <section v-else-if="page==='ats'" class="row g-3"><div class="col-lg-8"><form class="card border-0 shadow-sm" @submit.prevent="screenResume"><div class="card-body p-4"><h1 class="h3">ATS-style Résumé Screener</h1><p class="text-secondary">Keyword guidance only—not an automated hiring decision.</p><label class="form-label">Résumé text</label><textarea class="form-control mb-3" rows="10" maxlength="50000" v-model="ats.resume_text" required></textarea><label class="form-label">Job description</label><textarea class="form-control mb-3" rows="8" maxlength="30000" v-model="ats.job_description" required></textarea><button class="btn btn-primary">Screen resume</button></div></form></div><div class="col-lg-4"><div class="card border-0 shadow-sm h-100"><div class="card-body p-4"><template v-if="atsResult"><div class="display-4 fw-bold text-primary">{{ atsResult.score }}%</div><h2 class="h5">{{ atsResult.summary }}</h2><hr><h3 class="h6 text-success">Matched</h3><span v-for="x in atsResult.matched" class="badge text-bg-success me-1 mb-1">{{ x }}</span><h3 class="h6 text-danger mt-3">Missing</h3><span v-for="x in atsResult.missing" class="badge text-bg-light border me-1 mb-1">{{ x }}</span></template><p v-else class="text-secondary">Your analysis will appear here.</p></div></div></div></section>
    </main>
</div>
</template>

<script>
import { nextTick } from "vue";
import Chart from "chart.js/auto";
import StatusBadge from "./components/StatusBadge.vue";
import ListHeader from "./components/ListHeader.vue";
import ExportPanel from "./components/ExportPanel.vue";
import DriveTable from "./components/DriveTable.vue";
import ApplicationTable from "./components/ApplicationTable.vue";

export default {
  name: "App",
  components: { StatusBadge, ListHeader, ExportPanel, DriveTable, ApplicationTable },  data() {
    return {
      page: "home", user: null, loading: false, alert: { message: "", type: "info" },
      publicStats: { totals: {}, trends: { labels: [], values: [] }, funnel: { labels: [], values: [] }, skills: { labels: [], values: [] } },
      charts: [], dashboard: { metrics: {} }, search: "", companies: [], students: [], drives: [], applications: [], eligibleOnly: false,
      notifications: [], unreadCount: 0, showNotifications: false, notificationTimer: null, exportPollTimer: null,
      loginForm: { role: "student", email: "", password: "" }, registerRole: "student",
      degreeOptions: ["B.Tech", "M.Tech", "B.Sc", "M.Sc", "BCA", "MCA", "MBA", "BBA", "B.Com", "M.Com", "BA", "MA", "Diploma"],
      branchOptions: ["Computer Science", "Information Technology", "Electronics and Communication", "Electrical Engineering", "Mechanical Engineering", "Civil Engineering", "Chemical Engineering", "Artificial Intelligence", "Data Science", "Cybersecurity", "Business Administration", "Commerce", "Mathematics", "Physics", "General"],
      genderOptions: ["Female", "Male", "Other", "Prefer not to say"],
      studentRegister: { first_name: "", middle_name: "", last_name: "", email: "", password: "", confirm_password: "", contact: "", gender: "", dob: "", address_line1: "", address_line2: "", landmark: "", pincode: "", city: "", state: "", country: "India", course: "", branch: "", graduation_year: new Date().getFullYear() + 1, cgpa: "", skills: "", experience: "" },
      companyRegister: { company_name: "", industry: "", email: "", password: "", confirm_password: "", hr_first_name: "", hr_middle_name: "", hr_last_name: "", hr_email: "", hr_phone: "", website: "", headquarters: "", address_line1: "", address_line2: "", landmark: "", pincode: "", city: "", state: "", country: "India", description: "" },
      pincodeLoading: false, lastPincodeLookup: { student: "", company: "" }, pincodeMessage: { student: "", company: "" },
      showDriveForm: false, driveForm: {}, studentProfile: { user: {} }, companyProfile: {},
      ats: { resume_text: "", job_description: "" }, atsResult: null
    };
  },
  computed: {
    roleTitle() { return this.user ? this.user.role.charAt(0).toUpperCase() + this.user.role.slice(1) : ""; },
    today() { return new Date().toISOString().slice(0, 10); }
  },
  async mounted() {
    window.addEventListener("hashchange", () => this.route());
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/service-worker.js");
    await this.restoreSession();
    this.startNotificationPolling();
    await this.route();
  },
  beforeUnmount() {
    if (this.notificationTimer) clearInterval(this.notificationTimer);
    if (this.exportPollTimer) clearTimeout(this.exportPollTimer);
  },
  methods: {
    notify(message, type = "success") { this.alert = { message, type }; window.scrollTo({ top: 0, behavior: "smooth" }); },
    async api(path, options = {}) {
      const config = { credentials: "same-origin", ...options, headers: { ...(options.headers || {}) } };
      if (config.body && !(config.body instanceof FormData)) {
        config.headers["Content-Type"] = "application/json";
        config.body = JSON.stringify(config.body);
      }
      const response = await fetch(path, config);
      const payload = await response.json().catch(() => ({ ok: false, message: "Invalid server response." }));
      if (!response.ok || payload.ok === false) {
        const error = new Error(payload.message || `Request failed (${response.status})`);
        error.status = response.status;
        error.payload = payload;
        throw error;
      }
      return payload;
    },
    async withLoading(action) {
      this.loading = true;
      try { return await action(); }
      catch (error) { this.notify(error.message, "danger"); throw error; }
      finally { this.loading = false; }
    },
    startNotificationPolling() {
      if (!this.user || this.notificationTimer) return;
      this.notificationTimer = setInterval(() => this.loadNotifications(true), 30000);
    },
    async loadNotifications(silent = false) {
      if (!this.user) return;
      try {
        const result = await this.api("/api/notifications");
        this.notifications = result.data.items;
        this.unreadCount = result.data.unread_count;
      } catch (error) {
        if (!silent) this.notify(error.message, "danger");
      }
    },
    async toggleNotifications() {
      this.showNotifications = !this.showNotifications;
      if (this.showNotifications) await this.loadNotifications(true);
    },
    async openNotification(item) {
      if (!item.is_read) {
        await this.api(`/api/notifications/${item.id}/read`, { method: "PATCH" }).catch(() => {});
        item.is_read = true;
        this.unreadCount = Math.max(0, this.unreadCount - 1);
      }
      this.showNotifications = false;
      if (item.link_url) location.hash = item.link_url.replace(/^#/, "");
    },
    async markAllNotificationsRead() {
      await this.api("/api/notifications/read-all", { method: "PATCH" });
      this.notifications = this.notifications.map(item => ({ ...item, is_read: true }));
      this.unreadCount = 0;
    },
    async restoreSession() {
      const result = await this.api("/api/auth/me");
      this.user = result.data.user;
      if (this.user) await this.loadNotifications();
    },
    go(page) { location.hash = page; },
    async route() {
      let requested = location.hash.replace(/^#/, "") || (this.user ? "dashboard" : "home");
      const publicPages = new Set(["home", "analytics", "login", "register"]);
      if (!this.user && !publicPages.has(requested)) requested = "login";
      if (this.user && ["login", "register"].includes(requested)) requested = "dashboard";
      this.page = requested; this.search = "";
      await this.loadPage();
    },
    async loadPage() {
      const loaders = {
        home: this.loadPublicStats, analytics: this.loadPublicStats, dashboard: this.loadDashboard,
        "admin-companies": this.loadAdminCompanies, "admin-students": this.loadAdminStudents,
        "admin-drives": this.loadAdminDrives, "admin-applications": this.loadAdminApplications,
        "company-drives": this.loadCompanyDrives, "company-applications": this.loadCompanyApplications,
        "student-drives": this.loadStudentDrives, "student-applications": this.loadStudentApplications,
        profile: this.loadProfile
      };
      if (loaders[this.page]) await this.withLoading(loaders[this.page].bind(this)).catch(() => {});
    },
    async login() {
      await this.withLoading(async () => {
        const result = await this.api("/api/auth/login", { method: "POST", body: this.loginForm });
        this.user = result.data.user; this.loginForm.password = ""; await this.loadNotifications(); this.startNotificationPolling(); this.notify(result.message); this.go("dashboard");
      }).catch(() => {});
    },
    async logout() {
      await this.api("/api/auth/logout", { method: "POST" });
      this.user = null; this.dashboard = { metrics: {} }; this.notifications = []; this.unreadCount = 0; this.showNotifications = false;
      if (this.notificationTimer) clearInterval(this.notificationTimer);
      if (this.exportPollTimer) clearTimeout(this.exportPollTimer);
      this.notificationTimer = null;
      this.exportPollTimer = null;
      this.notify("Logged out.", "info"); this.go("home");
    },
    async registerStudent() {
      if (this.studentRegister.password !== this.studentRegister.confirm_password) return this.notify("Student passwords do not match.", "warning");
      await this.withLoading(async () => {
        const data = new FormData();
        Object.entries(this.studentRegister).forEach(([key, value]) => data.append(key, value ?? ""));
        const file = this.$refs.studentResume?.files[0]; if (file) data.append("resume", file);
        const result = await this.api("/api/auth/register/student", { method: "POST", body: data });
        this.notify(result.message); this.loginForm.email = this.studentRegister.email; this.loginForm.role = "student"; this.go("login");
      }).catch(() => {});
    },
    async registerCompany() {
      if (this.companyRegister.password !== this.companyRegister.confirm_password) return this.notify("Company passwords do not match.", "warning");
      await this.withLoading(async () => {
        const result = await this.api("/api/auth/register/company", { method: "POST", body: this.companyRegister });
        this.notify(result.message); this.loginForm.email = this.companyRegister.email; this.loginForm.role = "company"; this.go("login");
      }).catch(() => {});
    },
    digitsOnly(form, field, length = null) {
      let value = String(form[field] || "").replace(/\D/g, "");
      if (length) value = value.slice(0, length);
      form[field] = value;
    },
    async lookupPincodeDirect(pincode) {
      const response = await fetch(`https://api.postalpincode.in/pincode/${pincode}`);
      const payload = await response.json();
      if (!Array.isArray(payload) || payload[0]?.Status !== "Success" || !payload[0]?.PostOffice?.length) {
        throw new Error("No city or state was found for this pincode.");
      }
      const postOffice = payload[0].PostOffice[0];
      return {
        city: postOffice.District || postOffice.Name || "",
        state: postOffice.State || "",
        country: postOffice.Country || "India"
      };
    },
    async lookupPincode(form) {
      this.digitsOnly(form, "pincode", 6);
      const formKey = form === this.studentRegister ? "student" : "company";
      if (form.pincode.length !== 6) {
        this.lastPincodeLookup[formKey] = "";
        this.pincodeMessage[formKey] = "";
        return;
      }
      if (this.lastPincodeLookup[formKey] === form.pincode) return;
      this.lastPincodeLookup[formKey] = form.pincode;
      this.pincodeMessage[formKey] = "";
      this.pincodeLoading = true;
      try {
        const result = await this.api(`/api/public/pincode/${form.pincode}`);
        form.city = result.data.city;
        form.state = result.data.state;
        form.country = result.data.country || "India";
        this.pincodeMessage[formKey] = "City and state filled automatically.";
      } catch (error) {
        if (error.status === 502) {
          try {
            const result = await this.lookupPincodeDirect(form.pincode);
            form.city = result.city;
            form.state = result.state;
            form.country = result.country || "India";
            this.pincodeMessage[formKey] = "City and state filled automatically.";
            return;
          } catch (_fallbackError) {
            this.pincodeMessage[formKey] = "Auto-fill is unavailable right now. Please retry with a valid pincode.";
            return;
          }
        }
        this.pincodeMessage[formKey] = error.message;
      } finally {
        this.pincodeLoading = false;
      }
    },
    async loadPublicStats() {
      const result = await this.api("/api/public/stats"); this.publicStats = result.data; await nextTick(); this.renderCharts();
    },
    renderCharts() {
      this.charts.forEach(chart => chart.destroy()); this.charts = [];
      const make = (id, config) => { const el = document.getElementById(id); if (el) this.charts.push(new Chart(el, config)); };
      const base = { responsive: true, maintainAspectRatio: false };
      make("trendChart", { type: "line", data: { labels: this.publicStats.trends.labels, datasets: [{ label: "Placements", data: this.publicStats.trends.values, borderColor: "#2563eb", backgroundColor: "rgba(37,99,235,.15)", fill: true, tension: .3 }] }, options: base });
      make("funnelChart", { type: "doughnut", data: { labels: this.publicStats.funnel.labels, datasets: [{ data: this.publicStats.funnel.values, backgroundColor: ["#64748b", "#f59e0b", "#3b82f6", "#22c55e", "#ef4444"] }] }, options: base });
      make("skillsChart", { type: "bar", data: { labels: this.publicStats.skills.labels, datasets: [{ label: "Approved job mentions", data: this.publicStats.skills.values, backgroundColor: "#7c3aed" }] }, options: { ...base, indexAxis: "y", plugins: { legend: { display: false } } } });
    },
    async loadDashboard() {
      const result = await this.api(`/api/${this.user.role}/dashboard`); this.dashboard = result.data;
    },
    async pollExportStatus(exportId) {
      if (this.exportPollTimer) clearTimeout(this.exportPollTimer);
      const check = async () => {
        if (!this.user || !["student", "company"].includes(this.user.role)) return;
        try {
          const result = await this.api(`/api/${this.user.role}/export`);
          const latest = result.data;
          if (!latest || latest.id !== exportId) return;
          this.dashboard.latest_export = latest;
          if (latest.status === "completed") {
            this.notify("CSV export is ready to download.");
            await this.loadNotifications(true);
            return;
          }
          if (latest.status === "failed") {
            this.notify(latest.message || "CSV export failed.", "danger");
            await this.loadNotifications(true);
            return;
          }
          this.exportPollTimer = setTimeout(check, 4000);
        } catch (_error) {
          this.exportPollTimer = setTimeout(check, 8000);
        }
      };
      this.exportPollTimer = setTimeout(check, 4000);
    },
    async loadAdminCompanies() { const r = await this.api(`/api/admin/companies?q=${encodeURIComponent(this.search)}`); this.companies = r.data; },
    async loadAdminStudents() { const r = await this.api(`/api/admin/students?q=${encodeURIComponent(this.search)}`); this.students = r.data; },
    async loadAdminDrives() { const r = await this.api(`/api/admin/drives?q=${encodeURIComponent(this.search)}`); this.drives = r.data; },
    async loadAdminApplications() { const r = await this.api("/api/admin/applications"); this.applications = r.data; },
    async adminStatus(type, id, action) {
      if (!confirm(`${action} this record?`)) return;
      await this.withLoading(async () => { const r = await this.api(`/api/admin/${type}/${id}/status`, { method: "PATCH", body: { action } }); this.notify(r.message); await this.loadPage(); }).catch(() => {});
    },
    async adminDelete(type, id) {
      if (!confirm("Remove this record permanently?")) return;
      await this.withLoading(async () => { const r = await this.api(`/api/admin/${type}/${id}`, { method: "DELETE" }); this.notify(r.message); await this.loadPage(); }).catch(() => {});
    },
    async adminDriveAction(drive, action) {
      if (!confirm(`${action} ${drive.title}?`)) return;
      await this.withLoading(async () => {
        const url = `/api/admin/drives/${drive.id}${action === "delete" ? "" : "/status"}`;
        const r = await this.api(url, action === "delete" ? { method: "DELETE" } : { method: "PATCH", body: { action } });
        this.notify(r.message); await this.loadAdminDrives();
      }).catch(() => {});
    },
    csvToList(value) { return (value || "").split(",").map(item => item.trim()).filter(Boolean); },
    resetDriveForm() { this.driveForm = { id: null, title: "", job_type: "full-time", deadline: "", location: "", salary: "", salary_unit: "lpa", openings: 1, min_cgpa: "", eligible_degrees: "", eligible_branches: "", eligible_degrees_list: [], eligible_branches_list: [], eligible_years: "", skills_required: "", experience_required: "", benefits: "", description: "" }; },
    async loadCompanyDrives() { const r = await this.api("/api/company/dashboard"); this.dashboard = r.data; this.drives = r.data.drives; this.resetDriveForm(); },
    editDrive(drive) { this.driveForm = { ...drive, deadline: drive.deadline || "", eligible_degrees_list: this.csvToList(drive.eligible_degrees), eligible_branches_list: this.csvToList(drive.eligible_branches) }; this.showDriveForm = true; window.scrollTo({ top: 0, behavior: "smooth" }); },
    async saveDrive() {
      await this.withLoading(async () => {
        const editing = !!this.driveForm.id;
        const payload = {
          ...this.driveForm,
          eligible_degrees: (this.driveForm.eligible_degrees_list || []).join(", "),
          eligible_branches: (this.driveForm.eligible_branches_list || []).join(", ")
        };
        delete payload.eligible_degrees_list;
        delete payload.eligible_branches_list;
        const r = await this.api(editing ? `/api/company/drives/${this.driveForm.id}` : "/api/company/drives", { method: editing ? "PATCH" : "POST", body: payload });
        this.notify(r.message); this.showDriveForm = false; await this.loadCompanyDrives();
      }).catch(() => {});
    },
    async companyDriveAction(drive, action) {
      if (!confirm(`${action} ${drive.title}?`)) return;
      await this.withLoading(async () => { const r = await this.api(`/api/company/drives/${drive.id}/close`, { method: "PATCH" }); this.notify(r.message); await this.loadCompanyDrives(); }).catch(() => {});
    },
    async loadCompanyApplications() {
      const r = await this.api("/api/company/applications");
      this.applications = r.data.map(a => ({ ...a, interviews: a.interviews.map(i => ({ ...i, nextFeedback: i.feedback, nextResult: i.result })), nextStatus: ["shortlisted", "offer", "rejected", "placed"].includes(a.status) ? a.status : "shortlisted", nextFeedback: a.feedback, interviewAt: "", interviewLocation: "" }));
    },
    async updateApplication(application) {
      await this.withLoading(async () => { const r = await this.api(`/api/company/applications/${application.id}`, { method: "PATCH", body: { status: application.nextStatus, feedback: application.nextFeedback } }); this.notify(r.message); await this.loadCompanyApplications(); }).catch(() => {});
    },
    async scheduleInterview(application) {
      if (!application.interviewAt) return this.notify("Choose an interview date and time.", "warning");
      await this.withLoading(async () => { const r = await this.api(`/api/company/applications/${application.id}/interviews`, { method: "POST", body: { scheduled_at: application.interviewAt, mode: "online", location_or_link: application.interviewLocation } }); this.notify(r.message); await this.loadCompanyApplications(); }).catch(() => {});
    },
    async completeInterview(interview) {
      await this.withLoading(async () => { const r = await this.api(`/api/company/interviews/${interview.id}`, { method: "PATCH", body: { feedback: interview.nextFeedback, result: interview.nextResult } }); this.notify(r.message); await this.loadCompanyApplications(); }).catch(() => {});
    },
    async loadStudentDrives() { const r = await this.api(`/api/student/drives?q=${encodeURIComponent(this.search)}&eligible=${this.eligibleOnly ? 1 : 0}`); this.drives = r.data; },
    async applyDrive(drive) {
      await this.withLoading(async () => { const r = await this.api(`/api/student/drives/${drive.id}/apply`, { method: "POST", body: {} }); this.notify(r.message); await this.loadStudentDrives(); }).catch(() => {});
    },
    async loadStudentApplications() { const r = await this.api("/api/student/applications"); this.applications = r.data; },
    async withdrawApplication(application) {
      if (!confirm("Withdraw this application?")) return;
      await this.withLoading(async () => { const r = await this.api(`/api/student/applications/${application.id}/withdraw`, { method: "PATCH" }); this.notify(r.message); await this.loadStudentApplications(); }).catch(() => {});
    },
    async loadProfile() {
      const r = await this.api(`/api/${this.user.role}/dashboard`); this.dashboard = r.data;
      if (this.user.role === "student") this.studentProfile = JSON.parse(JSON.stringify(r.data.student));
      else this.companyProfile = JSON.parse(JSON.stringify(r.data.company));
    },
    async saveStudentProfile() {
      await this.withLoading(async () => { const data = new FormData(); const s = this.studentProfile; ["course", "branch", "graduation_year", "cgpa", "skills", "experience"].forEach(k => data.append(k, s[k] ?? "")); ["name", "contact", "address"].forEach(k => data.append(k, s.user[k] ?? "")); const file = this.$refs.profileResume?.files[0]; if (file) data.append("resume", file); const r = await this.api("/api/student/profile", { method: "PATCH", body: data }); this.studentProfile = r.data; this.user.name = r.data.user.name; this.notify(r.message); }).catch(() => {});
    },
    async saveCompanyProfile() {
      await this.withLoading(async () => { const r = await this.api("/api/company/profile", { method: "PATCH", body: this.companyProfile }); this.companyProfile = r.data; this.user.name = r.data.name; this.notify(r.message); }).catch(() => {});
    },
    async startExport() {
      await this.withLoading(async () => {
        const r = await this.api(`/api/${this.user.role}/export`, { method: "POST" });
        this.notify(r.message);
        await this.loadDashboard();
        if (r.data?.id) await this.pollExportStatus(r.data.id);
      }).catch(() => {});
    },
    async screenResume() {
      await this.withLoading(async () => { const r = await this.api("/api/tools/ats", { method: "POST", body: this.ats }); this.atsResult = r.data; }).catch(() => {});
    },
    formatDate(value) { return value ? new Date(value).toLocaleString() : "-"; }
  }
};
</script>
