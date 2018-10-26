/*
 * Task params:
 *
 * gulp --env development (default)
 * gulp --env production (minify/uglify version)
 *
 */

var basepath           = './';
var assets             = '../devday/devday/static';
var srcDir             = 'src';
var nodemodules        = 'node_modules';
var srcTest            = 'src-test';
var fs                 = require('fs');
var pkg                = JSON.parse(fs.readFileSync('./package.json'));

module.exports = {
    basepath: basepath,
    strings: {
        banner: [
            '/**',
            ' * Build on <%= new Date().getFullYear() %>-<%= new Date().getMonth() + 1 %>-<%= new Date().getDate() %>',
            ' * @package ' + pkg.name + '',
            ' * @version v' + pkg.version  + '',
            ' */',
            ''].join('\n')
    },


    environment: {
        string: 'env',
        default: { env: process.env.NODE_ENV || 'development' },
        production: 'production',
        development: 'development'
    },

    sass: {
        src:  srcDir + '/scss/style.scss',
        allsrc: [
                srcDir + '/scss/*.scss',
                srcDir + '/scss/components/*.scss',
                nodemodules + '@fortawesome/fontawesome-free/scss/*.scss'
        ],
        dest: assets + '/css',
        options: {
            autoprefixer: {
                browsers: [
                    'last 2 versions',
                    'safari 8',
                    'ie 10',
                    'ios 9',
                    'android 4'
                ],
                cascade: true
            }
        }
    },

    sasslint: {
        src: [
            srcDir + '/scss/*.scss'
        ],
        dest: './report',
        options: {
            config: srcDir + '/scss/.scss-lint.yml',
            filePipeOutput: 'scss-lint-report.json',
            reporterOutputFormat: 'JSON',
            maxBuffer: 600*1024,
            endless: true
        }
    },

    js: {
        src:  [
            nodemodules + '/jquery/dist/jquery.js',
            nodemodules + '/popper.js/dist/umd/popper.js',
            nodemodules + '/popper.js/dist/umd/popper-utils.js',
            nodemodules + '/bootstrap/dist/js/bootstrap.js',
            nodemodules + '/truncate.js/dist/truncate.js',
            nodemodules + '/qrcode-svg/lib/qrcode.js',
            nodemodules + '/cropperjs/dist/cropper.js',
            srcDir + '/js/core/class-instance-manager.js',
            srcDir + '/js/core/event-handler.js',
            srcDir + '/js/core/csrf-handler.js',
            srcDir + '/js/core/resize-listener.js',
            srcDir + '/js/components/image-modal.js',
            srcDir + '/js/components/collapse.js',
            srcDir + '/js/components/navbar.js',
            srcDir + '/js/components/qrcodelinks.js',
            srcDir + '/js/core/devday-registry.js',
        ],
        dest: assets + '/js',
        filename: 'main.js',
        minFilename: 'main.min.js'
    },

    jslint: {
        src: [
            srcDir + '/js/components/*.js',
            srcDir + '/js/core/*.js'
        ],
        options: {
            format: 'jslint',
            filePath: './report/js-lint-report.xml'
        }
    },

    jquery: {
        src:  [
            'bower_components/jquery/dist/jquery.js'
        ],
        dest: assets + '/js/'
    },

    images: {
        src:  [
            srcDir + '/assets/img/*.*',
            nodemodules + '/cropperjs/src/images/bg.png',
        ],
        dest: assets + '/img'
    },

    fonts: {
        src:  [
            srcDir + '/assets/fonts/**/*',
            nodemodules + '/@fortawesome/fontawesome-free/webfonts/*'
        ],
        dest: assets + '/fonts/'
    },

    browsersync: {
        // your array of files and folders to watch for changes
        watchjs: [
            assets + '/js/*.js'
        ]
    }


};
