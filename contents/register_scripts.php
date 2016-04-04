<?$ints = array();function cmp($a, $b) { if (strlen($a) == strlen($b)) { return 0; } return (strlen($a) > strlen($b)) ? -1 : 1;}uasort($ints, "cmp"); $myints = array();foreach($ints as $key => $value) { $pos = strpos($interest[0], $value); if($pos !== false) {$myints[] = $key;$interest[0] = substr($interest[0],0,$pos) . substr($interest[0],$pos+strlen($value),strlen($interest[0])); }}?>
<script language="javascript">
<!--
function onbeforesubmit()
{
return true;
}
//-->
</script>
<script language="javascript">
<!--
    var error;
var form_lanuage = 'de';
function is_46_valid(input)
{
    if(input == "")
    {
        error += "Anrede: Eingabe fehlt!\n";
        return false;
    }

    return true;
}
function is_1_valid(input)
{
    if(input == "")
    {
        error += "Vorname: Eingabe fehlt!\n";
        return false;
    }

    return true;
}
function is_2_valid(input)
{
    if(input == "")
    {
        error += "Nachname: Eingabe fehlt!\n";
        return false;
    }

    return true;
}
function is_3_valid(input)
{
    if(input == "")
    {
        error += "E-Mail: Eingabe fehlt!\n";
        return false;
    }

var emailPat=/^(.+)@(.+)$/
var specialChars="\\(\\)<>@,;:\\\\\\\"\\.\\[\\]"
var validChars="\[^\\s" + specialChars + "\]"
var quotedUser="(\"[^\"]*\")"
var ipDomainPat=/^\[(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\]$/
var atom=validChars + '+'
var word="(" + atom + "|" + quotedUser + ")"
var userPat=new RegExp("^" + word + "(\\." + word + ")*$")
var domainPat=new RegExp("^" + atom + "(\\." + atom +")*$")


var matchArray=input.match(emailPat)
if (matchArray==null) {
error += "E-Mail: Bitte geben Sie eine g\u00fcltige E-Mail Adresse an!\n"; // check @ and .
return false
}
var user=matchArray[1]
var domain=matchArray[2]

if (user.match(userPat)==null) {
error += "E-Mail: Bitte geben Sie eine g\u00fcltige E-Mail Adresse an!\n"; // username doesn't seem to be valid
return false
}

var IPArray=domain.match(ipDomainPat)
if (IPArray!=null) {
  for (var i=1;i<=4;i++) {
    if (IPArray[i]>255) {
error += "E-Mail: Bitte geben Sie eine g\u00fcltige E-Mail Adresse an!\n"; // Destination IP address is invalid
return false
    }
    }
    return true
}

var domainArray=domain.match(domainPat)
if (domainArray==null) {
error += "E-Mail: Bitte geben Sie eine g\u00fcltige E-Mail Adresse an!\n"; // The domain name doesn't seem to be valid
   return false
}

var atomPat=new RegExp(atom,"g")
var domArr=domain.match(atomPat)
var len=domArr.length


if (len<2) {
error += "E-Mail: Bitte geben Sie eine g\u00fcltige E-Mail Adresse an!\n"; // This address is missing a hostname
return false
}


    return true;
}
function is_56723_valid(input)
{
    if(input == "")
    {
        error += "Firma bzw. Universität: Eingabe fehlt!\n";
        return false;
    }

    return true;
}
function is_56722_valid(input)
{
    if(input == "")
    {
        error += "Position bzw. Studiengang: Eingabe fehlt!\n";
        return false;
    }

    return true;
}
function is_56724_valid(input)
{
    if(input == "")
    {
        error += "Wie bist Du auf den Dev Day aufmerksam geworden?: Eingabe fehlt!\n";
        return false;
    }

    return true;
}

function CheckInputs()
{
    var check_ok = true;
    error = "Fehler in der Eingabe!\n";
    check_ok = (is_46_valid(document.ProfileForm.inp_46.options[document.ProfileForm.inp_46.selectedIndex].value) && check_ok);
    check_ok = (is_1_valid(document.ProfileForm.inp_1.value) && check_ok);
    check_ok = (is_2_valid(document.ProfileForm.inp_2.value) && check_ok);
    check_ok = (is_3_valid(document.ProfileForm.inp_3.value) && check_ok);
    check_ok = (is_56723_valid(document.ProfileForm.inp_56723.value) && check_ok);
    check_ok = (is_56722_valid(document.ProfileForm.inp_56722.value) && check_ok);
    check_ok = (is_56724_valid(document.ProfileForm.inp_56724.value) && check_ok);
    if(check_ok == false)
        alert(error);
    return check_ok;
}
//-->
</script>


<script language="javascript">
function SubmitIt(){
                if(CheckInputs() == true){
                                if(window.onbeforesubmit)
                                                onbeforesubmit();
                                document.ProfileForm.submit();
                }
}

function MailIt(){
                if(CheckInputs()){
                                if((document.ProfileForm.subject.value=='') || (document.ProfileForm.msg.value==''))
                                                alert('Bitte f\u00fcr Sie die Nachrichtenfelder aus!');
                                else
                                                document.ProfileForm.submit();
    }
}

function FieldWithName(frm, fieldname, numofield)
{
    if(!numofield)
        numofield = 0;
    field_count = 0;
    for(i = 0; i < frm.elements.length; ++i)
    {
        if(frm.elements[i].name == fieldname)
        {
            if(field_count == numofield)
                return frm.elements[i];
            else
                field_count++;
        }
    }
}
function NumChecked(frm, fieldname)
{
        var count = 0;
        for(i = 0; i < frm.elements.length; ++i)
        {
                if(frm.elements[i].name == fieldname && frm.elements[i].checked == true)
                        ++count;
        }
        return count;
}
function NumSel(field)
{
    var count = 0;
    for(i = 0; i < field.length; ++i)
        if(field[i].selected == true) ++count;
    return count;
}
</script>

<script language="javascript">
var multiFields = new Array();
var dateFields = new Array();
multiFields["interest[]"] = "interest"
multiFields["optin"] = "optin"
var arr_interest = new Array();
</script><? if($alertbox != "") { echo "\r\n<script language=\"javascript\">\r\nalert(\"$alertbox\");</script>"; } ?>