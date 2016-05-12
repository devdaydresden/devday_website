<!-- BEGIN CONTACT -->
<section id="contact" class="contact-section">
  <div class="container">
    <h3>Jetzt in die Interessentenliste eintragen</h3>
    <h5 class="center">Du kannst dich für die Interessentenliste für zukünftige Events registrieren</h5>
    <form name="ProfileForm" onsubmit="return CheckInputs();" action="https://news.t-systems-mms.com/u/register.php" method=get class="contact-form">
      <input type=hidden name="CID" value="112554395">
      <input type=hidden name="SID" value="<?= isset($SID) ? $SID : ""; ?>">
      <input type=hidden name="UID" value="<?= isset($UID) ? $UID : ""; ?>">
      <input type=hidden name="f" value="36664"><input type=hidden name="p" value="2">
      <input type=hidden name="a" value="r">
      <input type=hidden name="el" value="<?= isset($el) ? $el : ""; ?>">
      <input type=hidden name="endlink" value="<?= isset($endlink) ? $endlink : ""; ?>">
      <input type=hidden name="llid" value="<?= isset($llid) ? $llid : ""; ?>">
      <input type=hidden name="c" value="<?= isset($c) ? $c : ""; ?>">
      <input type=hidden name="counted" value="<?= isset($counted) ? $counted : ""; ?>">
      <input type=hidden name="RID" value="<?= isset($RID) ? $RID : ""; ?>">
      <input type=hidden name="mailnow" value="<?= isset($mailnow) ? $mailnow : ""; ?>">
      <div class="main-form">
        <div class="row">
          <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
            <label>
              <select name="inp_46" size="1" required>
                <option value=""> </option>
                <option value="1"<?= (isset($inp_46) && ($inp_46 == "Herr")) ? " SELECTED" : ""; ?>>Herr</option>
                <option value="2"<?= (isset($inp_46) && ($inp_46 == "Frau")) ? " SELECTED" : ""; ?>>Frau</option>
              </select>
              <i><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#name-icon"></use></svg></i>
              <span class="uppercase">Anrede</span>
            </label>
          </div>
          <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
            <label>
              <input class="gray" type="text" name="inp_1" maxlength="60" value="<?= isset($inp_1) ? $inp_1 : ""; ?>" required>
              <i><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#name-icon"></use></svg></i>
              <span class="uppercase">Vorname</span>
            </label>
          </div>
          <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
            <label>
              <input class="gray" type="text" name="inp_2" maxlength="60" value="<?= isset($inp_2) ? $inp_2 : ""; ?>" required>
              <i><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#name-icon"></use></svg></i>
              <span class="uppercase">Name</span>
            </label>
          </div>
        </div>
        <div class="row">
          <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
            <label>
              <input class="gray" type="text" name="inp_3" maxlength="255" value="<?= isset($inp_3) ? $inp_3 : ""; ?>" required>
              <i><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#mail-icon"></use></svg></i>
              <span class="uppercase">E-Mail</span>
            </label>
          </div>
          <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
            <label>
              <input class="gray" type="text" maxlength="255" name="inp_56723" value="<?= isset($inp_56723) ? $inp_56723 : ""; ?>">
              <i><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#text-icon"></use></svg></i>
              <span class="uppercase">Firma / Hochschule</span>
            </label>
          </div>
          <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
            <label>
              <input class="gray" type="text" maxlength="255" name="inp_56722" value="<?= isset($inp_56722) ? $inp_56722 : ""; ?>">
              <i><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#text-icon"></use></svg></i>
              <span class="uppercase">Position / Studiengang</span>
            </label>
          </div>
        </div>
        <div class="row">
          <div class="col-lg-12">
            <label>
              <input type="text" maxlength="255" name="inp_56724" value="<?= isset($inp_56724) ? $inp_56724 : ""; ?>">
              <i><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#text-icon"></use></svg></i>
              <span>Wie bist Du auf den DevDay aufmerksam geworden?</span>
            </label>
          </div>
        </div>
      </div>
      <button class="btn1 btn--white big right" onclick="javascript:SubmitIt()">Jetzt Anmelden
        <span><svg role="img" fill="currentColor"><use xlink:href="svgicons/icons.svg#arrow-down"></use></svg></span>
      </button>
    <?php include 'register_scripts.php' ?>
    </form>
  </div>
  <div class="clearfix"></div>
</section>
<!-- END CONTACT -->
<?php
// vim: et sw=2 ts=2 ai si
?>
