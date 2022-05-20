const {series, src, dest} = require('gulp');
const autoprefixer = require('gulp-autoprefixer');
const concat = require('gulp-concat');
const header = require('gulp-header');
const plumber = require('gulp-plumber');
const sass = require('gulp-sass')(require('sass'));
const fs = require('fs');
const config = require('./gulp/config');

function build_js() {
    const result = src(config.js.src)
        .pipe(concat(config.js.filename))
        .pipe(dest(config.js.dest));

    if (fs.existsSync(config.js.dest + "/" + config.js.filename) && !fs.existsSync(config.js.dest + "/" + config.js.minFilename)) {
        fs.createReadStream(config.js.dest + "/" + config.js.filename)
            .pipe(fs.createWriteStream(config.js.dest + "/" + config.js.minFilename));
    }
    if (!fs.existsSync(config.js.dest + "/" + config.js.filename) && fs.existsSync(config.js.dest + "/" + config.js.minFilename)) {
        fs.createReadStream(config.js.dest + "/" + config.js.minFilename)
            .pipe(fs.createWriteStream(config.js.dest + "/" + config.js.filename));
    }

    return result;
}

function build_jquery() {
    return src(config.jquery.src).pipe(dest(config.jquery.dest));
}

// copy images
function build_images() {
    return src(config.images.src).pipe(dest(config.images.dest));
}

function build_fonts() {
    return src(config.fonts.src).pipe(dest(config.fonts.dest));
}

function build_sass() {
    return src(config.sass.src)
        .pipe(plumber())
        .pipe(sass())
        .pipe(header(config.strings.banner))
        .pipe(autoprefixer(config.sass.options.autoprefixer))
        .pipe(dest(config.sass.dest));
}

/**
 * Run all tasks needed for a build in defined order
 */
exports.default = series(
    build_jquery,
    build_js,
    build_sass,
    build_fonts,
    build_images
);

