module.exports = function(grunt) {
 
    // Project configuration.
    grunt.initConfig({
 
        //Read the package.json (optional)
        pkg: grunt.file.readJSON('package.json'),
 
        // Metadata.
        meta: {
            basePath: './',
            srcPath: './',
            deployPath: './deploy'
        },
 
        banner: '/*! <%= pkg.name %> - v<%= pkg.version %> - ' +
                '<%= grunt.template.today("yyyy-mm-dd") %>\n' +
                '* Copyright (c) <%= grunt.template.today("yyyy") %> ',
 
        // Task configuration.
        concat: {
            options: {
                stripBanners: true
            },
            dist: {
                src: ['<%= meta.srcPath %>jquery.min.js', '<%= meta.srcPath %>jquery.dropotron.min.js', '<%= meta.srcPath %>jquery.scrollgress.min.js', '<%= meta.srcPath %>skel.min.js', '<%= meta.srcPath %>skel-layers.min.js', '<%= meta.srcPath %>init.min.js', '<%= meta.srcPath %>map.min.js', '<%= meta.srcPath %>register.min.js'],
                dest: '<%= meta.deployPath %>scripts/app.js'
            }
        }
    });
 
    // These plugins provide necessary tasks.
    grunt.loadNpmTasks('grunt-contrib-concat');
 
    // Default task
    grunt.registerTask('default', ['concat']);
 
};
