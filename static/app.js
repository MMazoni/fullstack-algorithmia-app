const api_url='http://127.0.0.1:5000';

var app = new Vue({
    el: '#app',
    data: {
        error: null,
        avatar_loading: false,
        user: null,
        update_time: null,
        login: {
            email: null,
            password:null
        },
        token: null
    },

    methods: {
        register() {
            app.error = null;
            axios.post(api_url+'/register', {
                email: app.login.email,
                password: app.login.password
            }).then(response => {
                console.log(response);
                app.token = response.data.token;
                localStorage.token = app.token;
                app.user = response.data.user;
                app.updated_time = Date.now();
            }).catch(error => app.error = error.response.data.message);
        },
        login() {
            app.error = null;
            axios.post(api_url+'/login', {
                email: app.login.email,
                password: app.login.password
            }).then(response => {
                app.token = response.data.token;
                localStorage.toke = app.token;
                app.user = response.data.user;
                app.updated_time = Date.now();
            }).catch(err => app.error = err.response.data.message);
        },
        logOut() {
            app.error = null;
            app.user = null;
            app.login = {
                email: null,
                password: null
            };
            app.token = null;
            localStorage.token = null;
        },
        updatedUser() {
            app.error = null;
            axios.post(api_url+'/account', app.user, {
                headers: {
                    Authorization: 'Bearer: '+app.token
                }
            }).then(response => {
                app.error = "Your changes have been saved";
                app.user = response.data.user;
                app.updated_time = Date.now();
            }).catch(err => {
                if(err.response.status == 401) {
                    return app.logOut();
                }
                app.error = err.response.data.message;
            })
        },
        triggerAvatar() {
            this.$ref.avatar.click()
        },
        updatedAvatar() {
            var formData = new FormData();
            fileList = this.$ref.avatar.files;
            if (!fileList.length) 
                return;
            formData.append('avatar',fileList[0],fileList[0].name);
            const url = api_url+'/avatar';
            app.error = "Processing your image...";
            app.avatar_loading = true;
            axios.post(url, formData, {
                headers: {
                    Authorization: 'Bearer: ' + app.token,
                    'ContentType': 'multipart/form-data'
                }
            }).then(response => {
                app.error = null;
                app.avatar_loading = false;
                app.user = response.data.user;
                app.update_time = Date.now();
            }).catch(err => {
                if (err.response.status == 401) {
                    return app.logOut();
                }
                app.error = err.reponse.data.message;
                app.avatar_loading = false;
            });
        }
    },

    mounted() {
        var token = localStorage.token;
        if (token && token.split('.').length >= 3) {
            let data = JSON.parse(atob(token.split('.')[1]));
            let exp = new Date(data.exp*1000);
            if (new Date() < exp) {
                axios.get(api_url+'/account', {
                    headers: {
                        Authorization: 'Bearer: ' + token
                    }
                }).then(response => {
                    app.token = response.data.token;
                    localStorage.token = app.token;
                    app.user = response.data.user;
                    app.updated_time = Date.now();
                });
            }
        }
    }
});